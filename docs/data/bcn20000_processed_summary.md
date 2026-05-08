# BCN20000 Processed Summary

## Filtering Summary

- Rows before filtering: 18946
- Rows after dropping missing diagnosis_3: 17639
- Rows after all filtering: 17639
- Rows removed for missing diagnosis_3: 1307
- Rows removed for missing image files: 0
- Image existence match count: 17639 / 17639

## Overall Class Counts

- Melanoma: 4636
- Benign nevus: 5647
- Other lesion: 7356

## Split Class Counts

### train

- Melanoma: 3363
- Benign nevus: 3934
- Other lesion: 5055

### val

- Melanoma: 701
- Benign nevus: 778
- Other lesion: 1149

### test

- Melanoma: 572
- Benign nevus: 935
- Other lesion: 1152

## Unique lesion_id Counts by Split

- train: 3520
- val: 754
- test: 755

## Output Files

- master_metadata: `data/processed/bcn20000/master_metadata.csv`
- train: `data/processed/bcn20000/train.csv`
- val: `data/processed/bcn20000/val.csv`
- test: `data/processed/bcn20000/test.csv`
