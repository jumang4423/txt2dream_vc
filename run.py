from dotenv import load_dotenv
from colorama import Fore, Style
import gtts
import asyncio
import openai
import os
import sys
from datetime import datetime


# envloader
load_dotenv()
openai.api_key = os.getenv("OPEN_AI_APIKEY")
# vars
ERR_HEADER = "!!!!!! ERROR !!!!!!!"
INFO_HEADER = "*"
MODEL_NAME = "gpt-4"
TMP_FOLDER_LOC = "./tmp/"
OUTPUT_FOLDER_LOC = "./output/"
LANGUAGES = ['English', 'Hungarian', "Korean", 'Thai', 'Chinese', "Ukrainian", "Vietnamese", "French", "Italian", "Japanese"]
LANGUAGES_CODE = ["en", "hu", "ko", "th", "zh", "uk", "vi", "fr", "it", "ja"]


def info_print(msg):
    print(Fore.GREEN + INFO_HEADER + " " + msg + Style.RESET_ALL)


def err_print(msg):
    print(Fore.RED + ERR_HEADER + " " + msg + Style.RESET_ALL)


def basic_print(msg):
    print(Fore.WHITE + msg + Style.RESET_ALL)


def get_prompt_words():
    args_arr = sys.argv
    args_arr.pop(0)

    return args_arr


def welcome_txt():
    basic_print("txt2dream_vc is a tool that can translate your dream words into multiple language voice files.")
    basic_print("It's based on OpenAI's GPT-4 model, and Google's TTS API.")
    info_print("gpt model: " + MODEL_NAME)
    basic_print("created by jumang4423")


def gen_words_to_prompts(words):
    SYSTEM_PROMPT = 'make a sentense that is related to the word list given from user, you only return one sentense'
    messages = []
    messages.append({
        'role': 'system',
        'content': SYSTEM_PROMPT
        })
    messages.append({
        'role': 'user',
        'content': "word list: [" + ", ".join(words) + "]"
        })
    response = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=messages,
    )
    ai_response = response.choices[0].message.content

    return ai_response


async def translate_into_voice(text, lang, lang_code):
    SYSTEM_PROMPT = f"translate the text into {lang} language, you only return the translated text"
    messages = []
    messages.append({
        'role': 'system',
        'content': SYSTEM_PROMPT
        })
    messages.append({
        'role': 'user',
        'content': text
        })
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    ai_response = response.choices[0].message.content
    voice_file_name = f"{TMP_FOLDER_LOC}prompt_{lang}.mp3"
    tts = gtts.gTTS(ai_response, lang=lang_code)
    tts.save(voice_file_name)

    return voice_file_name, ai_response


async def generate_voice_file(prompt, lang, lang_code):
    basic_print("generating voice file for " + lang + "...")
    voice_file_name, prompt = await translate_into_voice(prompt, lang, lang_code)
    info_print("file: " + voice_file_name)
    info_print("prompt: " + prompt)
    basic_print("voice file generated")

    return voice_file_name


async def concat_audio_files(voice_file_names):
    TIMESTAMP_STR = datetime.now().strftime("%Y%m%d%H%M%S")
    new_file_name = f"{OUTPUT_FOLDER_LOC}output_{TIMESTAMP_STR}.mp3"
    basic_print("concatenating audio files...")
    os.system(f"ffmpeg -i \"concat:{'|'.join(voice_file_names)}\" -ac 2 {new_file_name}")

    # translate mp3 to aif
    basic_print("translating mp3 to aif...")
    os.system(f"ffmpeg -i {new_file_name} {new_file_name.replace('.mp3', '.aif')}")
    # removing mp3 file
    basic_print("removing mp3 file...")
    os.system(f"rm {new_file_name}")
    basic_print("concatenated audio file generated")

    return new_file_name.replace('.mp3', '.aif')


async def flash_tmp_folder():
    os.system(f"rm -rf {TMP_FOLDER_LOC}*")


async def main():
    welcome_txt()
    prompt_words = get_prompt_words()
    if prompt_words == []:
        err_print("no words given")
        exit(1)
    info_print("prompt words: " + str(prompt_words))
    basic_print("generating prompt...")
    prompt = gen_words_to_prompts(prompt_words)
    basic_print("prompt generated")
    info_print("prompt: " + prompt)

    user_ans = input("continue(y) or regenerate prompt(r)? (y/r): ")
    if user_ans == "r":
        await main()
        exit(0)
    info_print("generating voice files...")
    # clear cache
    info_print("clearing cache...")
    await flash_tmp_folder()
    info_print("cache cleared")
    # voice gen enumeration
    tasks = [generate_voice_file(prompt, lang, lang_code) for lang, lang_code in zip(LANGUAGES, LANGUAGES_CODE)]
    voice_file_names = await asyncio.gather(*tasks)
    # concat voice files into one file, with 1 secound silence between each file
    basic_print("concat voice files...")
    new_file_name = await concat_audio_files(voice_file_names)
    info_print("file: " + new_file_name)
    basic_print("concat voice files done")

if __name__ == "__main__":
    asyncio.run(main())
