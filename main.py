# TODO: changer les vidéo de bg
# TODO: changer le timer
# TODO: refaire l'intro
# TODO: changer comment audio and text
# TODO: mettre des niveaux (facile, moyen, expert)
# TODO: ajouter un QCM


import requests
import random
import os
from pprint import pprint

from moviepy.config import change_settings
from moviepy.editor import concatenate_videoclips
from ankipandas import Collection

from clip_generator import ClipGenerator, IntroOutro

NUMBER_OF_QUESTIONS = 6
NUMBER_OF_VIDEOS = 7

change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})


def get_question(anki_user_name="Mathieu", difficulty="UG::Sovereign_State") -> list:
    """
    get anki's notes details (country, capital, flag png, map png)
    :param anki_user_name: Mathieu if in french, Quizz if in english
    :return: List of anki's notes
    """
    col = Collection(user=anki_user_name)
    tags_list = col.notes.ntags.tolist()
    fields_list = col.notes.nflds.tolist()
    results = []
    for i in range(len(tags_list)):
        if "UG::Sovereign_State" and difficulty in tags_list[i]:
            notes_dict = {
                "Notes": fields_list[i],
                "Tags": tags_list[i]
                }

            results.append(notes_dict)

    return results


def random_bg_video() -> str:
    """
    Choisi une vidéo au hasard pour le background
    :return: path de la vidéo
    """
    video = random.choice(os.listdir("bg_videos/"))
    video_path = f"bg_videos/{video}"

    return video_path


if __name__ == "__main__":
    for i in range(NUMBER_OF_VIDEOS):
        print(f"Vidéo {i} en cours")
        bg_video = random_bg_video()
        duration = 0
        start_time = 0
        clips = []
        # intro = IntroOutro(data_path='sub_title_json/intro.json',
        #                   voice_path='voices/intro.mp3',
        #                   bg_video_path=bg_video,
        #                   start_time=0).subclip
        # clips.append(intro)
        #start_time += intro.duration

        for y in range(NUMBER_OF_QUESTIONS):

            if y <= 1:
                difficulty = 'facile'
            elif y <= 3:
                difficulty = 'moyen'
            else:
                difficulty = 'expert'

            questions = get_question(anki_user_name="Mathieu", difficulty=difficulty)

            data = random.choice(questions)
            print(data)

            if y == 2:
                like_subscribe_clip = IntroOutro(data_path='sub_title_json/message1.json',
                                                 voice_path='voices/message1.mp3',
                                                 bg_video_path=bg_video,
                                                 start_time=start_time).subclip
                clips.append(like_subscribe_clip)
                start_time += like_subscribe_clip.duration

            if y == 4:
                comment_clip = IntroOutro(data_path='sub_title_json/message2.json',
                                          voice_path='voices/message2.mp3',
                                          bg_video_path=bg_video,
                                          start_time=start_time).subclip
                clips.append(comment_clip)
                start_time += comment_clip.duration

            clip = ClipGenerator(bg_video_path=bg_video,
                                 data=data, start_time=start_time,
                                 question_number=f"question: {y+1}/{NUMBER_OF_QUESTIONS}",
                                 difficulty=difficulty
                                 )
            start_time += clip.clip_duration
            # try:
            #     clip = ClipGenerator(bg_video_path=bg_video, data=data, start_time=0)
            # except IndexError:
            #     print("index error")
            #     continue
            # else:
            #     duration += clip.subclip.duration
            clips.append(clip.subclip)

            if y == NUMBER_OF_QUESTIONS -1:
                comment_clip = IntroOutro(data_path='sub_title_json/message3.json',
                                          voice_path='voices/message3.mp3',
                                          bg_video_path=bg_video,
                                          start_time=start_time).subclip
                clips.append(comment_clip)
                start_time += comment_clip.duration

        final_video = concatenate_videoclips(clips)
        final_video.write_videofile(f"video_finale/videofinale{i}.mp4")
        print(f"Vidéo {i} terminé")




