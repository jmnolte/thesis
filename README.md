# Detecting hepatocellular carcinoma in non-alcoholic fatty liver disease patients using deep learning based radiomics

This repository contains the data along with the corresponding python code to reproduce all results presented in the project's preliminary [research report](https://github.com/jmnolte/thesis/tree/master/report). The research report was created as part of the author's master thesis at the University of Utrecht.

## Abstract

Hepatocellular carcimonia (HCC) is the most common liver cancer in adults and remains difficult to diagnose. Fortunately, recent advancements in the medical imaging domain have led to the development of two computational approaches that allow for the extraction of radiomic features from the raw images and aid the prediction of disease development. In the handcrafted approach, mathematically defined features are derived from the study's region of interest. In the deep learning approach, on the other hand, feature representation is learned through convolutional neural networks. This study compares the two approaches. Likewise, it aims to provide clinical utility to medical practicioners, thus interpreting the deep learning based features in the context of handcrafted radiomics. The preliminary results show that the deep learning based approach outperforms the handcrafted approach on all performance metrics. Furthermore, the results indicate that the loss of information induced by solely modeling the explainable deep features is not reflected in the model's performance metrics.

## License

The repository is licensed under the `apache-2.0` license.
