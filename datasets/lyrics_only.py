import torch
from torch.utils.data import Dataset
from mido import MidiFile, tick2second
import os
import numpy as np
import soundfile as sf




class LyricsOnly(Dataset):
    def __init__(self, ds_path, audio_segment_dir=None, audio_duration=5, ignore_empty=True, split_audio=True):
        self.ds_path = ds_path
        self.audio_duration = audio_duration
        self.ignore_empty = ignore_empty
        if audio_segment_dir is None:
            audio_segment_dir = os.path.join(ds_path, '..', 'audio_segments')
        self.audio_segment_dir = audio_segment_dir
        if split_audio:
            self._split_audio_to_segments()

    def _split_audio_to_segments(self):
        for dir in os.listdir(self.ds_path):
            dir_path = os.path.join(self.ds_path, dir)
            if os.path.isdir(dir_path):
                midi_file_path = os.path.join(dir_path, 'notes.mid')
                if not os.path.exists(midi_file_path):
                    continue
                print('working on song: {}'.format(dir))
                t2lyrics = self.cut_lyrics_to_parts(midi_file_path, self.audio_duration)

                # opening other audio files and cutting them to parts according to lyrics
                for audio_file in os.listdir(dir_path):
                    if audio_file.endswith('.ogg'):
                        audio_file_path = os.path.join(dir_path, audio_file)
                        audio, samplerate = sf.read(audio_file_path)
                        for i, ((t_start, t_end), lyrics) in enumerate(t2lyrics.items()):
                            if len(lyrics) > 0 or not self.ignore_empty:
                                # making sure all directories exist
                                if not os.path.isdir(self.audio_segment_dir):
                                    os.makedirs(self.audio_segment_dir)
                                processed_song_dir = os.path.join(self.audio_segment_dir, dir)
                                if not os.path.isdir(processed_song_dir):
                                    os.makedirs(processed_song_dir)
                                processed_section_dir = os.path.join(processed_song_dir, f'section_{i}_{lyrics}')
                                if not os.path.isdir(processed_section_dir):
                                    os.makedirs(processed_section_dir)
                                temp_audio = audio[int(t_start * samplerate):int(t_end * samplerate)]
                                sf.write(os.path.join(processed_section_dir, audio_file), temp_audio, samplerate)



    @staticmethod
    def cut_lyrics_to_parts(midi_file_path, audio_duration):
        """get lyrics from midi file, and cut it to audio_duration long parts
        :return dict: { (t_start, t_end): lyrics }"""
        t2lyrics = dict()
        # print(midi_file_path)
        mid = MidiFile(midi_file_path, clip=True)
        lyrics_track = [t for t in mid.tracks if t.name == 'PART VOCALS'][0]
        tempo_track = mid.tracks[0]
        assert tempo_track[0].type == 'set_tempo'

        i = 0
        j = 0
        current_beat = 0
        next_change = 0
        current_time = 0
        total_time = 0
        cur_lyrics = ''
        start_time = 0

        while i < len(lyrics_track):
            if next_change <= current_beat:
                #changing tempo
                if tempo_track[j].type != 'set_tempo':
                    j += 1
                    continue
                tempo = tempo_track[j].tempo
                j += 1
                next_change += tempo_track[j].time

            if lyrics_track[i].type == 'lyrics':
                cur_lyrics += lyrics_track[i].text
                cur_lyrics += ' '

            current_beat += lyrics_track[i].time
            current_time += tick2second(lyrics_track[i].time, mid.ticks_per_beat, tempo)
            total_time += tick2second(lyrics_track[i].time, mid.ticks_per_beat, tempo)

            if current_time >= audio_duration:
                cur_lyrics = cur_lyrics.replace('- ', '').replace('+ ', '').replace(' +', '').replace(' -', '').replace('#', '').replace('=', '')
                # TODO: fix this next line to give the actual t_start and t_end. currently its t_start + audio_duration so some words are cut in the middle.
                t2lyrics[(start_time, start_time + audio_duration)] = cur_lyrics
                cur_lyrics = ''
                current_time = 0
                start_time = total_time
            i += 1
        return t2lyrics



def main():
    ds_path = os.path.join('songs')
    dataset = LyricsOnly(ds_path)
    print('done')


if __name__ == '__main__':
    main()