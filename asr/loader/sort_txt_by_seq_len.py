"""
Sort a train.txt like file by it's audio files sequence length.
"""

import os
import sys

from multiprocessing import Pool, Lock
from tqdm import tqdm

from asr.util import storage
from asr.loader.load_sample import load_sample


DATASETS_PATH = '../datasets/speech_data'


def _sort_txt_by_seq_len(txt_path, max_length=1700):
    """Sort a train.txt like file by it's audio files sequence length.

    Args:
        txt_path (str): Path to the `train.txt`.
        max_length (int): Positive integer. Max length for a feature vector to keep.
            Set to `0` to keep everything.

    Returns:
        Nothing.
    """

    # Read train.txt file.
    with open(txt_path, 'r') as f:
        lines = f.readlines()
        read_length = len(lines)

        # Setup threadpool.
        num_processes = 8
        lock = Lock()
        buffer = []   # Output buffer.

        with Pool(processes=num_processes) as pool:
            for result in tqdm(pool.imap_unordered(__feature_length, lines, chunksize=8),
                               desc='Reading audio samples', total=len(lines), file=sys.stdout,
                               unit='samples', dynamic_ncols=True):
                lock.acquire()
                buffer.append(result)
                lock.release()

        # Sort by sequence length.
        buffer = sorted(buffer, key=lambda x: x[0])

        # Remove samples longer than `max_length` points.
        if max_length > 0:
            original_length = len(buffer)
            buffer = [s for s in buffer if s[0] < 1750]
            print('Removed {:,d} samples from training.'.format(original_length - len(buffer)))

        # Remove sequence length.
        buffer = ['{} {}'.format(p, l) for _, p, l in buffer]

    # Write back to file.
    assert read_length == len(buffer)
    storage.delete_file_if_exists(txt_path)
    with open(txt_path, 'w') as f:
        f.writelines(buffer)

    with open(txt_path, 'r') as f:
        assert len(f.readlines()) == read_length, \
            'Something went wrong writing the data back to file.'
        print('Successfully sorted {} lines of {}'.format(read_length, txt_path))


def __feature_length(line):
    # Python multiprocessing helper method.
    wav_path, label = line.split(' ', 1)
    length = int(load_sample(os.path.join(DATASETS_PATH, wav_path))[1])
    return length, wav_path, label


if __name__ == '__main__':
    # Path to `train.txt` file.
    _txt_path = os.path.join('./data', 'train.txt')

    # Display dataset stats.
    _sort_txt_by_seq_len(_txt_path)