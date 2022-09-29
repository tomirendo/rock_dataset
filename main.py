from datasets import LyricsOnly

ds_path = 'datasets/songs'

def main():
    ds = LyricsOnly(ds_path=ds_path)

if __name__ == '__main__':
    main()
