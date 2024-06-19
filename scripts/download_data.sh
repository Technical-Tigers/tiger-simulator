#!/bin/bash
mkdir ../data

mkdir ../data/llm
wget https://github.com/Azure/AzurePublicDataset/raw/master/data/AzureLLMInferenceTrace_code.csv -P ../data/llm
wget https://github.com/Azure/AzurePublicDataset/raw/master/data/AzureLLMInferenceTrace_conv.csv -P ../data/llm

mkdir ../data/functions
wget https://azurecloudpublicdataset2.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2019/azurefunctions-dataset2019.tar.xz -P ../data/functions
tar -xf ../data/functions/azurefunctions-dataset2019.tar.xz -C ../data/functions/