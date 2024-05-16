import whisper
from pprint import pprint
import json

def speech_to_text():
    model = whisper.load_model("medium")
    result = model.transcribe("voices/message2.mp3", word_timestamps=True)
    pprint(result)
    print(result["text"])

    words = []

    for segment in result['segments']:
        for word in segment['words']:
            print(word)
            words.append({'word': word['word'],
                          'start': word['start'],
                          'end': word['end']})

    with open('sub_title_json/message2.json', 'w') as f:
        json.dump(words, f, indent=4)


if __name__ == "__main__":
    speech_to_text()


