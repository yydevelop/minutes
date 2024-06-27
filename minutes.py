import base64
import os
import time
import openai
import moviepy.editor as mp
from pydub import AudioSegment


class AudioProcessor:
    def __init__(self, openai_api_key, whisper_model="whisper-1", whisper_language="ja", openai_model="gpt-3.5-turbo"):
        openai.api_key = openai_api_key
        self.whisper_model = whisper_model
        self.whisper_language = whisper_language
        self.openai_model = openai_model

    def convert_mp4_to_mp3(self, mp4_file_path):
        mp3_file_path = os.path.splitext(mp4_file_path)[0] + '.mp3'
        audio = mp.AudioFileClip(mp4_file_path)
        audio.write_audiofile(mp3_file_path)
        time.sleep(1)
        return mp3_file_path

    def transcribe_audio(self, mp3_file_path):
        with open(mp3_file_path, 'rb') as audio_file:
            transcription = openai.Audio.transcribe(
                self.whisper_model, audio_file, language=self.whisper_language)
        return transcription.text

    def save_text_to_file(self, text, output_file_path):
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(text)

    def split_audio(self, mp3_file_path, interval_ms, output_folder):
        if not os.path.isfile(mp3_file_path):
            print(f"File does not exist: {mp3_file_path}")
            return []

        audio = AudioSegment.from_file(mp3_file_path)
        file_name = os.path.splitext(os.path.basename(mp3_file_path))[0]

        mp3_file_path_list = []
        n_splits = len(audio) // interval_ms

        for i in range(n_splits + 1):
            start, end = i * interval_ms, (i + 1) * interval_ms
            split = audio[start:end]
            output_file_name = f"{output_folder}_{i}.mp3"
            split.export(output_file_name, format="mp3")
            mp3_file_path_list.append(output_file_name)

        return mp3_file_path_list

    def create_meeting_minutes(self, transcriptions, output_file_path, prompt_text, other_text):
        pre_summary = "".join(transcriptions)
        prompt = f"""
        {prompt_text}

        # その他の会議情報
        {other_text}

        # 会議文字起こしテキスト
        {pre_summary}
        """

        print("議事録を作成中です...")
        response = openai.ChatCompletion.create(
            model=self.openai_model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.0,
        )
        self.save_text_to_file(
            response['choices'][0]['message']['content'], f"{output_file_path}_minutes.txt")

    def process_file(self, file_path, output_path, interval_ms=600_000):
        if not os.path.isfile(file_path):
            print("File does not exist")
            return ""

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.mp4':
            mp3_file_path = self.convert_mp4_to_mp3(file_path)
            file_path = mp3_file_path
            ext = '.mp3'

        if ext == '.mp3':
            mp3_file_path_list = self.split_audio(
                file_path, interval_ms, output_path)
            transcriptions = [self.transcribe_audio(
                mp3_path) for mp3_path in mp3_file_path_list]
            # mp3ファイルを削除
            for mp3_path in mp3_file_path_list:
                os.remove(mp3_path)

            # transcriptionsを結合
            transcription_text = "\n".join(transcriptions)

            # ファイル出力
            output_file_path = f"{output_path}_transcription.txt"
            self.save_text_to_file(transcription_text, output_file_path)

            return "\n".join(transcriptions)

        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        print("Unsupported file type")
        return ""

    def get_prompt_from_file(self, prompt_folder="./"):
        prompt_files = [f for f in os.listdir(
            prompt_folder) if os.path.isfile(os.path.join(prompt_folder, f))]
        if not prompt_files:
            return ""

        # ファイルが1つの場合はそのファイルを使用
        if len(prompt_files) == 1:
            with open(os.path.join(prompt_folder, prompt_files[0]), 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print("使用するプロンプト:")
            for i, file in enumerate(prompt_files):
                print(f"{i+1}: {file}")

            selected_index = int(
                input("番号を入力: "))

            # 存在しない番号が入力された場合は空文字列を返す
            if selected_index < 1 or selected_index > len(prompt_files):
                return ""
            else:
                # 対応するファイルを読み込む
                with open(os.path.join(prompt_folder, prompt_files[selected_index-1]), 'r', encoding='utf-8') as f:
                    return f.read()


def main():
    # 環境変数OPENAI_API_KEYからAPIキーを取得
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        print("環境変数OPENAI_API_KEYが設定されていません")
        return

    processor = AudioProcessor(api_key, whisper_model="whisper-1",
                               whisper_language="ja", openai_model="gpt-3.5-turbo")

    prompt_text = processor.get_prompt_from_file(prompt_folder="./prompt/")

    # ファイルパスを入力
    file_path = input("ファイルパスを入力してください: ")
    output_path = os.path.splitext(file_path)[0]

    # 他の会議情報を入力
    # 空行で入力を終了
    print("その他の会議情報を入力してください。（空行で終了）")
    print("入力を終了するには空行を入力してください")
    other_input = []
    while True:
        line = input()
        if not line:
            break
        other_input.append(line)
    other_text = "\n".join(other_input)

    transcriptions = processor.process_file(
        file_path, output_path=output_path)

    processor.create_meeting_minutes(
        transcriptions, output_path, prompt_text, other_text)


if __name__ == "__main__":
    main()
