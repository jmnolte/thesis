# Early Stage Hepatocellular Carcinoma Diagnosis Using a 3D Convolutional Neural Network Ensemble

This repository contains the [scripts](https://github.com/jmnolte/thesis/tree/master/scripts) to reproduce all results presented in the project's final [report](https://github.com/jmnolte/thesis/tree/master/report). The report was created as part of the author's master thesis at Utrecht University and was produced in cooperation with Medisch Spectrum Twente and the University of Twente.

## Abstract

For hepatocellular carcinoma (HCC) patients, early-stage diagnosis continues to be the most important predictor of survival. However, lesion detection typically only occurs at an advanced stage and continues to be largely affected by radiologists' experience. To facilitate patient survival, this study proposed a novel computer-aided diagnosis (CAD) system using data on 243 patients (759 observations) with compensated liver cirrhosis. Particularly, four individual 3-dimensional convolutional neural networks were trained, and their predictions aggregated in an ensemble to further enhance accurate tumor diagnosis. The models were validated on an independent internal test set, and their performance was evaluated with respect to a number of standard evaluation metrics. Despite the promising findings attained in our preliminary investigation, the results showed that all four individual models displayed limited diagnostic capabilities, with their predictions remaining largely inferior to the naive prediction of the study's majority class. Meanwhile, the ensemble of the four models displayed greater discriminatory power between HCC and common liver cirrhosis but still failed to accurately infer cancer prevalence. While the proposed CAD thus yielded limited diagnostic value of HCC, its accurate evaluation may have been severely constrained by the study's limitations in computing resources, thus highlighting the need for future research to reevaluate the CAD’s viability.

## Data

Data was retroactivelly collected from a cohort of liver cirrhosis patients who underwent MRI screening for HCC surveillance between March 2011 and September 2022 at Medisch Spectrum Twente in Enschede, the Netherlands. In total, the study comprised 759 observations from 243 patients of which 80 observations comprised diagnosed HCC.

## Results

<p align="center">
  <img alt="Light" title="Receiver Operating Characteristic Curves" src="https://github.com/jmnolte/thesis/blob/master/results/model_diagnostics/roc_pr_curves/roc_curves.png" width="45%">
&nbsp; &nbsp; &nbsp; &nbsp;
  <img alt="Dark" title="Precision-Recall Curves" src="https://github.com/jmnolte/thesis/blob/master/results/model_diagnostics/roc_pr_curves/prec_recall_curves.png" width="45%">
</p>

- The models' deduced feature representations failed to capture the tumor's heterogeneous phenotype (see above figures).
- The proposed CAD thus provided limited diagnostic viability.
- However, study was severely limited by the available computing resources. For the analysis, all images had to be downsampled to less than 1% of the original image's resolution to fit them into the GPUs' memory.

## Directions for Future Work

- Considering the limitations in computing ressources, future work should consider a two-stage segmentation classification pipeline, where the patient's liver is first segmented and the resulting cropped image is then classified.
- Additionally, the procedure could be further enhanced by feeding image patches to the models.

## Reproducing the Results

### Requirements

To reproduce the results presented in the project's [report](https://github.com/jmnolte/thesis/tree/master/report), access to a Nvidia GPU with a minimum of 8GB VRAM is required. However, training on a single GPU significantly increases processing time. To enhance training, the authors thus recommend the use of four Nvidia GPUs with 12GB VRAM each. All required package versions are listed in [requirements.txt](https://github.com/jmnolte/thesis/blob/master/requirements.txt). To ensure a fully reproducible workflow, install them by running `pip install -r requirements.txt` in your command line.

### Workflow

All scripts are self contained and should be executed from the command line or using a slurm scheduler in the case of access to a high performance computing cluster. If the latter is provided, please adjust the paths in the given sh files and submit them using the following order:

1. Training: `training10.sh`, `training18.sh`, `training34.sh`, `training50.sh`, `trainingEns.sh`
2. Inference: `inference10.sh`, `inference18.sh`, `inference34.sh`, `inference50.sh`, `inferenceEns.sh`
3. Diagnostics: `diagnostics10.sh`, `diagnostics18.sh`, `diagnostics34.sh`, `diagnostics50.sh`, `diagnosticsEns.sh`

If access to a high performance cluster is not provided, please execute the aforementioned scripts using `torchrun` directly from your command line, omitting the `--standalone` flag and the `--nproc_per_node` indicator.

Note that according to the number of accessiable GPUs and the total amount of accessiable VRAM per GPU, the batch size (i.e., per GPU) and the number of accumulation steps may need to be adjusted. For an overview of the hyperparameter settings used in this study, please refer to Appendix A in the study's [report](https://github.com/jmnolte/thesis/tree/master/report).

## License

The repository is licensed under the `apache-2.0` license.
