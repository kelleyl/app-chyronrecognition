import math
import uuid
import PIL
import clams
import cv2
from clams.app import ClamsApp
from clams.restify import Restifier
from mmif.vocabulary import AnnotationTypes, DocumentTypes
import utils
from mmif import Mmif, View
import pytesseract

APP_VERSION = 0.1


class ChyronRecognition(ClamsApp):
    def _appmetadata(self):
        metadata = {
            "name": "Chyron Recognition",
            "description": "This tool detects chyrons and generates time segments.",
            "app_version": str(APP_VERSION),
            "app_license": "MIT",
            "url": f"http://mmif.clams.ai/apps/chyrondetect/{APP_VERSION}",
            "identifier": f"http://mmif.clams.ai/apps/chyrondetect/{APP_VERSION}",
            "input": [{"@type": DocumentTypes.VideoDocument, "required": True}],
            "output": [
                {"@type": AnnotationTypes.TimeFrame, "properties": {"frameType": "string"}},
                {"@type": DocumentTypes.TextDocument},
                {"@type": AnnotationTypes.Alignment},
            ],
            "parameters": [
                {
                    "name": "timeUnit",
                    "type": "string",
                    "choices": ["frames", "milliseconds"],
                    "default": "frames",
                    "description": "Unit for output typeframe.",
                },
                {
                    "name": "sampleRatio",
                    "type": "integer",
                    "default": "5",
                    "description": "Frequency to sample frames.",
                },
                {
                    "name": "minFrameCount",
                    "type": "integer",
                    "default": "10",  # minimum value = 1 todo how to include minimum
                    "description": "Minimum number of frames required for a timeframe to be included in the output",
                },
                {
                    "name": "threshold",
                    "type": "number",
                    "default": ".5",
                    "description": "Threshold from  0-1, lower accepts more potential chyrons. ",
                }
            ],
        }
        return clams.AppMetadata(**metadata)

    def _annotate(self, mmif:Mmif, **kwargs):
        video_filename = mmif.get_document_location(DocumentTypes.VideoDocument)
        config = self.get_configuration(**kwargs)
        unit = config["timeUnit"]
        new_view:View = mmif.new_view()
        self.sign_view(new_view, config)
        new_view.new_contain(
            AnnotationTypes.TimeFrame,
            timeUnit=unit,
            document=mmif.get_documents_by_type(DocumentTypes.VideoDocument)[0].id
        )
        new_view.new_contain(
            DocumentTypes.TextDocument
        )
        new_view.new_contain(
            AnnotationTypes.Alignment
        )
        chyron_results = self.run_chyrondetection(video_filename, **kwargs)
        for chyron_result in chyron_results:
            timeframe_annotation = new_view.new_annotation(AnnotationTypes.TimeFrame)
            timeframe_annotation.add_property("start", chyron_result["start_frame"])
            timeframe_annotation.add_property("end", chyron_result["end_frame"])
            timeframe_annotation.add_property("frameType", "chyron")

            text_document = new_view.new_textdocument(chyron_result["text"])
            
            align_annotation = new_view.new_annotation(AnnotationTypes.Alignment)
            align_annotation.add_property("source", timeframe_annotation.id)
            align_annotation.add_property("target", text_document.id)
        return mmif

    @staticmethod
    def process_chyron(start_seconds, end_seconds, start_frame, end_frame, frame_list, chyron_box):
        # frames = [frame_list[0], frame_list[math.floor(len(frame_list) / 2)], frame_list[-1]]
        texts = []
        for _id, frame in enumerate(frame_list):
            bottom_third = frame[math.floor(.6 * frame.shape[0]):,:]
            img = utils.preprocess(bottom_third)
            img = PIL.Image.fromarray(img)
            if chyron_box:
                img = img[chyron_box[1]:chyron_box[3],chyron_box[0]:chyron_box[2]] 
            # img.save(f"sample_images/{guid}_{_id}.png")
            text = pytesseract.image_to_string(
                img,
                config="-c tessedit_char_whitelist='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.\n '"
            )
            texts.append(text)
        text = max(texts, key=len)
        return {
            "start_seconds":start_seconds,
            "end_seconds": end_seconds,
            "start_frame":start_frame,
            "end_frame": end_frame,
            "chyron_box": chyron_box,
            "text": text,
        }

    @staticmethod
    def frame_has_chyron(frame, threshold):
        return utils.get_chyron(frame, threshold)

    @staticmethod
    def filter_boxes(box_list, frame_height):
        if not box_list:
            return None
        bottom_third_boxes = [box for box in box_list if box[1] > (math.floor(.4 * frame_height))]
        return max(bottom_third_boxes, key=lambda x: (x[3]-x[1])*(x[2]-x[0]), default=None)

    def run_chyrondetection(
        self, video_filename, **kwargs
    ): 
        sample_ratio = int(kwargs.get("sampleRatio", 10))
        min_duration = int(kwargs.get("minFrameCount", 10))
        threshold = .5 if "threshold" not in kwargs else float(kwargs["threshold"])

        cap = cv2.VideoCapture(video_filename)
        counter = 0
        chyrons = []
        in_chyron = False
        start_frame = None
        start_seconds = None
        frame_list = []
        chyron_box = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if counter > 30 * 60 * 60 * 5: # five hours
                if in_chyron:
                    frame_list.append(frame)
                    if counter - start_frame > min_duration:
                        chyrons.append(
                            self.process_chyron(
                                start_seconds = start_seconds,
                                end_seconds = cap.get(cv2.CAP_PROP_POS_MSEC),
                                start_frame = start_frame,
                                end_frame = counter,
                                frame_list = frame_list,
                                chyron_box = chyron_box
                            )
                        )
                        frame_list = []
                break
            if counter % sample_ratio == 0:
                result = self.frame_has_chyron(frame, threshold=threshold)
                chyron_box = self.filter_boxes(result, frame.shape[0])
                if chyron_box:  # has chyron
                    frame_list.append(frame)
                    if not in_chyron:
                        in_chyron = True
                        start_frame = counter
                        start_seconds = cap.get(cv2.CAP_PROP_POS_MSEC)
                else:
                    if in_chyron:
                        in_chyron = False
                        if counter - start_frame > min_duration:
                            chyrons.append(
                                self.process_chyron(
                                    start_seconds = start_seconds,
                                    end_seconds = cap.get(cv2.CAP_PROP_POS_MSEC),
                                    start_frame = start_frame,
                                    end_frame = counter,
                                    frame_list = frame_list,
                                    chyron_box = chyron_box
                                )
                            )
                            frame_list = []
            counter += 1
        return chyrons


if __name__ == "__main__":
    chyron_tool = ChyronRecognition()
    chyron_service = Restifier(chyron_tool)
    chyron_service.run()
