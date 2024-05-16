from dataclasses import dataclass, field
import os
from pprint import pprint
import random
import html
from functools import partial
from collections import defaultdict
import json

import elevenlabs
import numpy as np
import os

from elevenlabs.client import ElevenLabs
import pyttsx3
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import vfx, ColorClip, ImageClip
from moviepy.config import change_settings

MAP_PHOTO_PATH = r'C:\Users\mathi\AppData\Roaming\Anki2\Quizz\collection.media'
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")


# Donne le chemin de imagemagick utilisé par MoviePy
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

@dataclass
class ClipGenerator:
    data: defaultdict[dict] = field(default_factory=lambda: defaultdict(dict))
    bg_video_path: str = ""
    start_time: int = 0
    timer: int = 5
    question_number: str = ""
    difficulty: str = " "

    def __post_init__(self):

        # creation du clip
        clip = VideoFileClip(self.bg_video_path)

        # récupération des questions et réponses
        self.question: str = "A quel pays appartient ce drapeau?"
        self.right_answer: str = html.unescape(self.data['Notes'][0])
        map_path: str = os.path.join(MAP_PHOTO_PATH, self.data['Notes'][5].replace('<img src=', '').replace('"', '').replace(' />', '').replace('>', '').replace('svg', 'png'))

        # création des fichiers audio et des AudioFileClip
        # question_audio = self._create_voices(text=self.question, path="voices/question.mp3")
        # answer_audio = self._create_voices(text=self.right_answer, path="voices/right_answer.mp3")
        question_audio = AudioFileClip("voices/question_flag.mp3")
        answer_audio = self._create_voices_elevenlabs(text=self.right_answer, path="voices/right_answer.mp3")

        #création du subclip de la video
        self.end_time = question_audio.duration + self.timer + answer_audio.duration
        self.subclip = clip.subclip(self.start_time, self.start_time + self.end_time)
        self.clip_duration = self.subclip.duration

        # ajout de la question et des réponses à l'audio
        self.subclip = self._add_voices(audio_clips=[question_audio, answer_audio],
                                        subclip=self.subclip)

        end_text_time = self.end_time - answer_audio.duration

        # Ajout de l'image de la map au clip
        self.map_image = ImageClip(map_path).set_start(0).set_duration(end_text_time).set_position(('center', 770))
        self.subclip = CompositeVideoClip([self.subclip, self.map_image])

        # Ajout du timer pour laisser le temps de répondre
        self.subclip = self._add_timer(video_file='5_seconds_timer.mp4',
                                       subclip=self.subclip,
                                       start_time=question_audio.duration)

        # création des TextClip
        textclips = []
        starts_time = []
        durations = []

        color = 'white'
        size = 1000
        bg_size = 1010
        fontsize = 70

        # durations.extend([end_text_time, end_text_time])
        #
        # starts_time.extend([self.start_time, self.start_time])

        # Creation des text de la question
        text_clip = self._create_text(text=self.question, size=size, fontsize=fontsize, color=color)
        text_clip_bg = self._create_text(text=self.question,
                                         color='black',
                                         stroke_color='black',
                                         stroke_width=10,
                                         size=bg_size,
                                         fontsize=fontsize)

        textclips.extend([text_clip_bg, text_clip])
        starts_time.extend([0, 0])
        durations.extend([end_text_time, end_text_time])

        # Creation des text du numéro de la question ex: 1/6
        text_clip = self._create_text(text=self.question_number, size=size, fontsize=fontsize, color=color)
        text_clip_bg = self._create_text(text=self.question_number,
                                         color='black',
                                         stroke_color='black',
                                         stroke_width=10,
                                         size=bg_size,
                                         fontsize=fontsize)

        textclips.extend([text_clip_bg, text_clip])
        starts_time.extend([0, 0])
        durations.extend([self.end_time, self.end_time])

        # Creation des text de la difficulté
        text_clip = self._create_text(text=self.difficulty, size=size, fontsize=fontsize, color=color)
        text_clip_bg = self._create_text(text=self.difficulty,
                                         color='black',
                                         stroke_color='black',
                                         stroke_width=10,
                                         size=bg_size,
                                         fontsize=fontsize)

        textclips.extend([text_clip_bg, text_clip])
        starts_time.extend([0, 0])
        durations.extend([self.end_time, self.end_time])

        # Ajout des textes à choix multiple
        choices = self.get_multiple_choices(number_of_choices=3)

        choices_text = []
        choices_starts_time = []
        choices_duration = []

        for choice in choices:

            text_clip = self._create_text(text=html.unescape(choice), size=size, fontsize=fontsize, color=color)
            text_clip_bg = self._create_text(text=html.unescape(choice),
                                             color='black',
                                             stroke_color='black',
                                             stroke_width=10,
                                             size=bg_size,
                                             fontsize=fontsize)

            choices_text.extend([text_clip_bg, text_clip])
            choices_starts_time.extend([0,0])
            choices_duration.extend([end_text_time, end_text_time])

        # Ajout de la bonne réponse aux réponses choix multible

        text_clip = self._create_text(text=self.right_answer, size=size, fontsize=fontsize, color=color)
        text_clip_bg = self._create_text(text=self.right_answer,
                                         color='black',
                                         stroke_color='black',
                                         stroke_width=10,
                                         size=bg_size,
                                         fontsize=fontsize)

        choices_text.extend([text_clip_bg, text_clip])
        choices_starts_time.extend([0, 0])
        choices_duration.extend([end_text_time, end_text_time])

        # randomize la position des choix multiples
        y_pos = 1100
        choices_positions = []
        choices_effects = []

        for i in range(int(len(choices_text) / 2)):
            choices_positions.append([(39, y_pos), (40, y_pos)])
            choices_effects.extend(['translate', 'translate'])
            y_pos += 150

        random.shuffle(choices_positions)

        new_choices_positions = []
        for position in choices_positions:
            new_choices_positions.extend(position)

        textclips.extend(choices_text)
        starts_time.extend(choices_starts_time)
        durations.extend(choices_duration)


        # creation du text de la bonne réponse
        text_clip = self._create_text(text=self.right_answer, color='green')
        text_clip_bg = self._create_text(text=self.right_answer,
                                         color='black',
                                         stroke_color='black',
                                         stroke_width=10,
                                         size=1010,
                                         fontsize=70)

        textclips.extend([text_clip_bg, text_clip])
        starts_time.extend([end_text_time, end_text_time])
        durations.extend([answer_audio.duration, answer_audio.duration])

        effects_list: list[str] = ['translate', 'translate',
                                   '', '',
                                   'translate', 'translate',
                                   *choices_effects,
                                   'translate', 'translate']

        # ajout des TextClip au SubClip
        self.subclip = self._add_texts(clip=self.subclip,
                                       textclips=textclips,
                                       start_time=starts_time,
                                       duration=durations,
                                       position=[(39, 419), (40, 420),
                                                 (300, 200), (300, 200),
                                                 (-300, 200), (-300, 200),
                                                 *new_choices_positions,
                                                 (39, 969), (40, 970),
                                                 ],
                                       effect=effects_list)

    def _create_voices(self, text: str, path: str):
        """
        generate voice from a text via pyttsx3 to spare elevenlabs credits
        :param text: text to speech
        :param path: where to save the audio
        :return: clip audio
        """
        engine = pyttsx3.init()
        engine.save_to_file(text, path)
        engine.runAndWait()
        engine.stop()

        audio = AudioFileClip(path)

        return audio

    def _create_voices_elevenlabs(self, text: str, path: str):
        """
        Text to speech with elevenlabs
        :param text: Text to speech
        :param path: where to save the audio
        :return: Audioclip
        """
        #elevenlabs.set_api_key(ELEVENLABS_API_KEY)

        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

        # Gestion des settings de la voix, nom de la voix: Adam
        voice = elevenlabs.Voice(
            voice_id="pNInz6obpgDQGcFmaJgB",
            settings=elevenlabs.VoiceSettings(
                stability=0.2,
                similarity_boost=0.75
            )
        )

        # Génère l'Audio et l'enregistre
        audio = client.generate(
            text=text,
            voice=voice,
            model="eleven_multilingual_v2"
        )

        elevenlabs.save(audio, path)

        audio = AudioFileClip(path)

        return audio

    def _create_text(self,
                     text: str,
                     color: str = 'white',
                     stroke_color: str = None,
                     stroke_width: int = 0,
                     size: int = 1000,
                     fontsize: int = 70) -> object:
        """
        création des textes
        :param text: text pour créer un TextClip
        :return: TextClip
        """
        textclip = TextClip(
            txt=text,
            color=color,
            bg_color='transparent',
            font='Arial-Bold-Italic',
            fontsize=fontsize,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            size=(size, None),
            method='caption',
            align='center')

        return textclip

    def _add_voices(self, audio_clips: list, subclip):
        if len(audio_clips) > 1:
            audio_mix = CompositeAudioClip([audio_clips[0],
                                            audio_clips[1].set_start(audio_clips[0].duration + self.timer),
                                            ])
            subclip = subclip.set_audio(audio_mix)
        else:
            subclip = subclip.set_audio(audio_clips[0])

        return subclip

    def _add_texts(self, clip: object,
                   textclips: list[object],
                   start_time: list[int],
                   duration: list[int],
                   position: list[tuple],
                   effect: list[str]) -> object:
        text_clip_list = []
        for i in range(len(textclips)):
            pos = position[i]

            if effect[i] == 'translate':
                pos = partial(self.translation_effect, position=position[i])

            textclip = textclips[i].set_pos(pos).set_start(start_time[i]).set_duration(duration[i])

            if effect[i] == 'zoom':
                textclip = textclip.resize(lambda t: self.zoom_effect(t))

            text_clip_list.append(textclip)

        clip = CompositeVideoClip([clip, *text_clip_list])

        return clip

    def translation_effect(self, t, position: tuple[int], duration: int = 0.5):
        # Start and end positions of the text
        start_pos = (-1000, position[1])
        end_pos = position

        # Calculate x and y positions based on elapsed time and total duration
        # Linear interpolation is used to determine the position of the text at any given time
        if t/duration < 1:
            x = int(start_pos[0] + t / duration * (end_pos[0] - start_pos[0]))
            y = int(start_pos[1] + t / duration * (end_pos[1] - start_pos[1]))
        else:
            x = end_pos[0]
            y = end_pos[1]

        return x, y

    def zoom_effect(self, t, duration: int = 0.5):
        # Starting scale factor
        start_scale = 0.1
        # End scale factor (the size to which the text should grow)
        end_scale = 1
        # Calculate the scaling factor based on elapsed time and total duration
        if t/duration < 1:
            scale_factor = start_scale + t / duration * (end_scale - start_scale)
        else:
            return end_scale

        return scale_factor

    def _add_timer(self, video_file: str, subclip, start_time: int):
        """
        Retire le fond vert du timer
        :param video_file: fichier vidéo fond vert à traiter
        :return: la videoclip sans le fond vert
        """
        clip = VideoFileClip(video_file)
        masked_clip = clip.fx(vfx.mask_color, color=[0, 255, 8], thr=180, s=5)
        clip_green_screen_removed = CompositeVideoClip([masked_clip]).set_duration(clip.duration - 1).set_pos((400, 1200))

        clip = CompositeVideoClip([subclip, clip_green_screen_removed.set_start(start_time)])

        return clip

    def get_multiple_choices(self, number_of_choices: int = 2):
        with open("data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        choices = []

        for i in range(number_of_choices):
            choices.append(random.choice(html.unescape(data['Pays'])))

        return choices


@dataclass
class IntroOutro:
    bg_video_path: str = ''
    start_time: int = 0,
    data_path: str = '',
    voice_path: str = ''

    def __post_init__(self):
        with open(self.data_path, 'r') as f:
            self.text = json.load(f)

        linelevel_subtitles = self.split_text_into_lines()

        clip = VideoFileClip(self.bg_video_path)
        audio = AudioFileClip(self.voice_path)
        self.subclip = clip.subclip(t_start=self.start_time, t_end=(audio.duration + self.start_time))

        self.clip_duration = self.subclip.duration

        frame_size = clip.size

        all_linelevel_splits = []
        for line in linelevel_subtitles:
            out_clips = self.create_caption(line, frame_size)
            all_linelevel_splits.extend(out_clips)

        self.subclip = CompositeVideoClip([self.subclip, *all_linelevel_splits])
        self.subclip = self.subclip.set_audio(audio)

    def split_text_into_lines(self):
        maxchars = 7
        # maxduration in seconds
        MaxDuration = 1
        # Split if nothing is spoken (gap) for these many seconds
        MaxGap = 1.5

        subtitles = []
        line = []
        line_duration = 0
        line_chars = 0

        for idx, word_data in enumerate(self.text):
            word = html.unescape(word_data["word"])
            start = word_data["start"]
            end = word_data["end"]

            line.append(word_data)
            line_duration += end - start

            temp = " ".join(item["word"] for item in line)

            # Check if adding a new word exceeds the maximum character count or duration
            new_line_chars = len(temp)

            duration_exceeded = line_duration > MaxDuration
            chars_exceeded = new_line_chars > maxchars
            if idx > 0:
                gap = word_data['start'] - self.text[idx - 1]['end']
                # print (word,start,end,gap)
                maxgap_exceeded = gap > MaxGap
            else:
                maxgap_exceeded = False

            if duration_exceeded or chars_exceeded or maxgap_exceeded:
                if line:
                    subtitle_line = {
                        "word": " ".join(html.unescape(item["word"]) for item in line),
                        "start": line[0]["start"],
                        "end": line[-1]["end"],
                        "textcontents": line
                    }
                    subtitles.append(subtitle_line)
                    line = []
                    line_duration = 0
                    line_chars = 0

        if line:
            subtitle_line = {
                "word": " ".join(html.unescape(item["word"]) for item in line),
                "start": line[0]["start"],
                "end": line[-1]["end"],
                "textcontents": line
            }
            subtitles.append(subtitle_line)

        return subtitles

    def create_caption(self, textJSON, framesize, font="Arial-Bold-Italic", color='white', highlight_color='yellow',
                       stroke_color='black', stroke_width=1.5):
        wordcount = len(textJSON['textcontents'])
        full_duration = textJSON['end'] - textJSON['start']

        word_clips = []
        xy_textclips_positions = []

        x_pos = 30
        y_pos = 200
        line_width = 0  # Total width of words in the current line
        frame_width = framesize[0]
        frame_height = framesize[1]

        x_buffer = frame_width * 1 / 10
        y_buffer = frame_height * 1/5

        max_line_width = frame_width - 2 * (x_buffer)

        fontsize = 110  # 7.5 pe rcent of video height

        space_width = ""
        space_height = ""

        for index, wordJSON in enumerate(textJSON['textcontents']):
            duration = wordJSON['end'] - wordJSON['start']
            word_clip = TextClip(html.unescape(wordJSON['word']), font=font, fontsize=fontsize, color=color, stroke_color=stroke_color,
                                 stroke_width=stroke_width).set_start(textJSON['start']).set_duration(full_duration)
            bg_clip = TextClip(wordJSON['word'], font=font, fontsize=fontsize, color='black', stroke_color='black',
                                 stroke_width=10).set_start(textJSON['start']).set_duration(full_duration)
            word_clip_space = TextClip(" ", font=font, fontsize=fontsize, color=color).set_start(
                textJSON['start']).set_duration(full_duration)
            word_width, word_height = word_clip.size
            space_width, space_height = word_clip_space.size
            if line_width + word_width + space_width <= max_line_width:
                # Store info of each word_clip created
                xy_textclips_positions.append({
                    "x_pos": x_pos + x_buffer,
                    "y_pos": y_pos + y_buffer,
                    "width": word_width,
                    "height": word_height,
                    "word": html.unescape(wordJSON['word']),
                    "start": wordJSON['start'],
                    "end": wordJSON['end'],
                    "duration": duration
                })

                word_clip = word_clip.set_position((x_pos + x_buffer, y_pos + y_buffer))
                bg_clip = bg_clip.set_position((x_pos + x_buffer, y_pos + y_buffer))
                word_clip_space = word_clip_space.set_position((x_pos + word_width, y_pos + y_buffer))
                x_pos = x_pos + word_width + space_width

            word_clips.extend([bg_clip, word_clip])
            word_clips.append(word_clip_space)

        for highlight_word in xy_textclips_positions:
            word_clip_highlight = TextClip(html.unescape(highlight_word['word']), font=font, fontsize=fontsize, color=highlight_color,
                                           stroke_color=stroke_color, stroke_width=stroke_width).set_start(
                highlight_word['start']).set_duration(highlight_word['duration'])
            word_clip_highlight = word_clip_highlight.set_position((highlight_word['x_pos'], highlight_word['y_pos']))
            word_clips.append(word_clip_highlight)

        return word_clips


if __name__ == "__main__":
    y_pos = 900
    choices_positions = [(39, y_pos), (40, y_pos)]
    choices_effects = ['translate', 'translate']

    for i in range(2):
        y_pos += 50
        choices_positions.extend([(39, y_pos), (40, y_pos)])
        choices_effects.extend(['translate', 'translate'])

    pprint(choices_positions)
    pprint(choices_effects)

