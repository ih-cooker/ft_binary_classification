# ft_binary_classification
アミノ酸配列がDNA-binding motifsを持つかどうかの二値分類を行います。
アミノ酸配列のデータとしてUniprot https://www.uniprot.org/ のデータを使用します

SentencePieceでトークナイズされたアミノ酸配列をTfidfVectorizerでベクトル化、LogisticRegressionで分類します。

Uniplotでは配列の特徴は「FT   DNA_BIND」のように記載されています。　　

なぜDNA-binding motifsを対象にするかというと種を問わず広く保存されていそうだからという理由と、ただ単に思い出深いモチーフだからです。　　

ただし一口にDNA binding と言っても様々な種類がありコンセンサス配列も様々です。「FT   DNA_BIND」のデータが5584個でその中でもHomeoboxのデータが1372個も含まれるのでデータに偏りがあるかもしれません。　　

評価の結果からもホメオドメインの配列を重要視している印象です。

# Run
以下でUniprotからのデータをダウンロードし、解凍します。

```
$ wget https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_sprot.dat.gz
$ gunzip uniprot_sprot.dat.gz

```

その後、以下を実行してください。

```
$ python ft_binary_classification.py uniprot_sprot.dat
```


# Requirement

Python 3.6.9　　

sentencepiece   0.1.96　　

scikit-learn     0.24.2　　

