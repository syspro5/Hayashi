# !/usr/bin/env python
# coding: utf-8
import io
import os
import csv
import pandas as pd
from google.cloud import storage
from moviepy.editor import *
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types


class transcription():
    bucket_name = 'systemproject2019'

    def __init__(self, video_file):
        self.video_file = video_file
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "auth.json"

        self.mp4towav()
        self.gcsupload()

    def transcribe_gcs(self, gcs_uri):

        client = speech.SpeechClient()

        audio = types.RecognitionAudio(uri=gcs_uri)

        config = types.RecognitionConfig(
            # sample_rate_hertz=48000,
            encoding=enums.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
            language_code='ja-JP',
            enable_word_time_offsets=True,  # 時間オフセット
            enable_automatic_punctuation=True
        )

        operation = client.long_running_recognize(config, audio)

        print('Waiting for operation to complete...')
        operationResult = operation.result()

        speech_data = []
        transcript_data = []

        # 時間情報と共に字幕を取得
        for result in operationResult.results:
            alternative = result.alternatives[0]
            """
            print(u'Transcript: {}'.format(alternative.transcript))
            print('Confidence: {}'.format(alternative.confidence))
            """

            flg = 0
            for word_info in alternative.words:
                word = word_info.word
                start_time = word_info.start_time
                end_time = word_info.end_time

                word_str = '{}'.format(word)
                start_time_str = '{}'.format(
                    start_time.seconds + start_time.nanos * 1e-9)
                end_time_str = '{}'.format(
                    end_time.seconds + end_time.nanos * 1e-9)

                if flg == 0:
                    head = start_time_str
                    flg = 1
                end = end_time_str

                speech_data.append(
                    [word_str.split('|')[0], start_time_str, end_time_str])

            transcript_data.append(
                ['{}'.format(alternative.transcript), head, end])

        # 単語ごとに分割
        df = pd.DataFrame(speech_data, columns=[
                          'word', 'start_time', 'end_time'])
        df.to_csv('.\\source\\speech.csv', encoding='utf_8_sig')

        # 文章ごとに分割
        dft = pd.DataFrame(transcript_data, columns=[
            'word', 'start_time', 'end_time'])
        dft.to_csv('.\\source\\transcript.csv', encoding='utf_8_sig')

    def mp4towav(self):
        # .mp4 -> .wav
        video = VideoFileClip(self.video_file)
        self.audio_file = self.video_file.replace('.mp4', '.wav')
        video.audio.write_audiofile(self.audio_file,
                                    ffmpeg_params=['-ac', '1'])  # Convert to mono

    def gcsupload(self):
        # upload to google cloud strage
        client = storage.Client()
        bucket = client.get_bucket(self.bucket_name)
        blob = bucket.blob("audio.wav")
        blob.upload_from_filename(self.audio_file)


if __name__ == '__main__':
    t = transcription(".\\source\\video.mp4")
    t.transcribe_gcs("gs://systemproject2019/audio.wav")
