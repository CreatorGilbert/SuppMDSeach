import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import (
    Features,
    EntitiesOptions,
    EmotionOptions,
)

apikey = "o2tycULC2S7RN94_LsWFxBCXQz0qUTgxlU6wtdbOQVBh"
apiurl = "https://gateway.watsonplatform.net/natural-language-understanding/api"

natural_language_understanding = NaturalLanguageUnderstandingV1(
    version="2019-07-12", iam_apikey=apikey, url=apiurl
)


def get_emotion(text):
    response = natural_language_understanding.analyze(
        text=text, features=Features(emotion=EmotionOptions())
    ).get_result()

    return response
