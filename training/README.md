# Training

How the leaf-disease model in `../model/` was made.

1. Download the [PlantVillage dataset](https://www.kaggle.com/datasets/emmarex/plantdisease)
   and extract the class folders into `data/PlantVillage/` (this folder is git-ignored).
2. Split it 80/20 into train and validation sets:
   ```bash
   python training/split_train_val.py
   ```
3. Run `train_mobilenetv2_leaf_disease.ipynb` (a GPU such as a Colab T4 is recommended).
4. Copy the resulting `mobilenetv2_leaf_disease_final.pth` into `model/`. If you change the classes,
   update `model/index_to_name.json` and the `REMEDY_MAP` in `app.py` to match.
