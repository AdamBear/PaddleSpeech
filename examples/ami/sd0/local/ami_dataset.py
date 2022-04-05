# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import collections
import json

from paddle.io import Dataset

from paddleaudio.backends import load as load_audio
from paddleaudio.datasets.dataset import feat_funcs


class AMIDataset(Dataset):
    """
    AMI dataset.
    """

    meta_info = collections.namedtuple(
        'META_INFO', ('id', 'duration', 'wav', 'start', 'stop', 'record_id'))

    def __init__(self, json_file: str, feat_type: str='raw', **kwargs):
        """
        Ags:
            json_file (:obj:`str`): Data prep JSON file.
            labels (:obj:`List[int]`): Labels of audio files.
            feat_type (:obj:`str`, `optional`, defaults to `raw`):
                It identifies the feature type that user wants to extrace of an audio file.
        """
        if feat_type not in feat_funcs.keys():
            raise RuntimeError(
                f"Unknown feat_type: {feat_type}, it must be one in {list(feat_funcs.keys())}"
            )

        self.json_file = json_file
        self.feat_type = feat_type
        self.feat_config = kwargs
        self._data = self._get_data()
        super(AMIDataset, self).__init__()

    def _get_data(self):
        with open(self.json_file, "r") as f:
            meta_data = json.load(f)
        data = []
        for key in meta_data:
            sub_seg = meta_data[key]["wav"]
            wav = sub_seg["file"]
            duration = sub_seg["duration"]
            start = sub_seg["start"]
            stop = sub_seg["stop"]
            rec_id = str(key).rsplit("_", 2)[0]
            data.append(
                self.meta_info(
                    str(key),
                    float(duration), wav, int(start), int(stop), str(rec_id)))
        return data

    def _convert_to_record(self, idx: int):
        sample = self._data[idx]

        record = {}
        # To show all fields in a namedtuple: `type(sample)._fields`
        for field in type(sample)._fields:
            record[field] = getattr(sample, field)

        waveform, sr = load_audio(record['wav'])
        waveform = waveform[record['start']:record['stop']]

        feat_func = feat_funcs[self.feat_type]
        feat = feat_func(
            waveform, sr=sr, **self.feat_config) if feat_func else waveform

        record.update({'feat': feat})

        return record

    def __getitem__(self, idx):
        return self._convert_to_record(idx)

    def __len__(self):
        return len(self._data)
