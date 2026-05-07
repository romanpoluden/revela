# BCN20000 Dataset Decision

## Decision

Use BCN20000 as the primary dataset for the first Revela CNN MVP.

## Reason

BCN20000 is a strong fit for a dermoscopic lesion classifier. It supports the MVP classes:

- Melanoma
- Benign nevus
- Other lesion

## Why not SCIN / Fitzpatrick17k for this model

SCIN and Fitzpatrick17k are useful for eczema/dermatitis, clinical-style images, and skin-tone metadata, but they differ from BCN20000 in image domain. Combining dermoscopic lesion datasets with clinical/web-style datasets may introduce domain shift.

## MVP scope

The CNN MVP is dermoscopic-only.

The app should say:
"Upload a dermoscopic skin-lesion image."

Not:
"Upload any skin photo."

## Known limitations

- No skin-tone metadata in BCN20000.
- Not suitable for skin-tone fairness claims.
- Not suitable for eczema/dermatitis classification.
- Not clinically validated.
- Educational prototype only.