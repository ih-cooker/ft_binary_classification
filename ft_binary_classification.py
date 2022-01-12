import sys
import random
import sentencepiece as spm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import svm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
import numpy as np

# 各データ準備


def ft_in(feature, uni_whole):

    with open(uni_whole, 'rt') as f:
        flead = f.read()
        fsp = flead.split("//\n")
    # 真核生物かつDNA結合モチーフを持つものがいくつあるか.データ中の割合は？
    f_eu = [s for s in fsp if "OC   Eukaryota" in s]
    print("真核生物のデータ数", len(f_eu))  # 194064

    chain_in_eu = [s for s in f_eu if "FT   CHAIN" in s]
    print("真核かつchainのデータ数", len(chain_in_eu))  # 187022

    ft_in_ch = [s for s in chain_in_eu if feature in s]
    print("真核かつchainかつDNA_BINDデータ数", len(ft_in_ch))  # 5584

    ft_in_hb = [s for s in ft_in_ch if '/note="Homeobox"' in s]
    print("真核かつchainかつDNA_BINDかつHomeoboxデータ数", len(ft_in_hb))  # 1372

    ft_in_ht = [s for s in ft_in_ch if "H-T-H motif" in s]
    print("真核かつchainかつDNA_BINDかつH-T-H motifデータ数", len(ft_in_ht))  # 457

    ft_in_at = [s for s in ft_in_ch if "A.T hook " in s]
    print("真核かつchainかつDNA_BINDかつA.T hook データ数", len(ft_in_at))  # 60

    ft_in_zn = [s for s in ft_in_ch if "FT   ZN_FING" in s]
    print("真核かつchainかつDNA_BINDかつZN_FINGデータ数", len(ft_in_zn))  # 672

    # 全データで目的モチーフを持つもの、持たないもので極端な偏りが出ないように。
    # 対象FTデータ:対象FTネガティブなデータが　1：2　の割合　 len(sample_list)--> 16752
    no_ft = [s for s in chain_in_eu if feature not in s]
    print("chain_in_euの中でDNA_BIND持たないデータ数", len(no_ft))  # 181438

    noft_sample = random.sample(no_ft, len(ft_in_ch) * 2)
    noft_sample.extend(ft_in_ch)
    random.shuffle(noft_sample)
    sample_list = noft_sample
    print(len(sample_list))

    # リスト内で情報部とaa部に分け、添え字アクセスできるように
    separated = []
    for i in sample_list:
        separated.append(i.split("SQ   "))

    for i, p in enumerate(separated):
        tmp = p[1].split("\n")
        del tmp[0]
        temp2 = "".join(tmp)
        separated[i][1] = temp2.replace(" ", "")

    # separated[i][1]のアミノ酸配列が重複していたら除く
    separate = []
    unique = []
    for p in separated:
        if p[1] not in unique:
            unique.append(p[1])
            separate.append(p)
    print("aa重複のないデータ数", len(unique))

    # trein test に分ける
    test_p_list = separate[0:2000]
    train_p_list = separate[2000:]
    print("テストデータ数", len(test_p_list), "トレーニングデータ数", len(train_p_list))

    # AA部分をｔｘｔに変換 特定のFT（今はDNAbinding）に対する正解リストも用意
    train_aa = []
    train_ans = []
    for i in range(len(train_p_list)):
        # 情報部分に該当FTがふくまれるか
        train_ans.append(feature in train_p_list[i][0])
        # AA部分を分ける
        train_aa.append(train_p_list[i][1])
    train_p_aat = "\n".join(train_aa)
    with open("train_p_aa.txt", "w") as f:
        f.write(train_p_aat.lower())

    test_aa = []
    test_ans = []
    for i in range(len(test_p_list)):
        # 情報部分に該当FTがふくまれるか
        test_ans.append(feature in test_p_list[i][0])
        # AA部分を分ける
        test_aa.append(test_p_list[i][1])

    test_p_aat = "\n".join(test_aa)
    with open("test_p_aa.txt", "w") as f:
        f.write(test_p_aat.lower())

    return train_aa, train_ans, test_aa, test_ans

# 単語分割、ベクトル化、LogisticRegressionもしくはSVMで分類


def classification(train_aa, train_ans, test_aa, test_ans):

    tc = 0
    for tmp in test_ans:
        if tmp is True:
            tc += 1
    print("True/test_ans の割合", (tc / len(test_ans)))

    # センテンスピースで単語分割
    spm.SentencePieceTrainer.train(
        "--input=train_p_aa.txt --model_prefix=train_p_aa_m --vocab_size=8000"
    )
    sp = spm.SentencePieceProcessor()
    sp.Load("train_p_aa_m.model")

    # SentencePieceでトークナイズされたアミノ酸配列をTfidfVectorizerでベクトル化、LogisticRegressionで分類

    def tokenize(text):
        text = text.lower()
        return sp.encode(text, out_type=str, enable_sampling=True, alpha=0.1)

    vectorizer = TfidfVectorizer(tokenizer=tokenize)
    print("Transform開始")
    train_matrix = vectorizer.fit_transform(train_aa)
    test_matrix = vectorizer.transform(test_aa)

    print("学習開始")
    # clf = svm.SVC(class_weight="balanced")
    clf = LogisticRegression(class_weight="balanced")
    clf.fit(train_matrix, train_ans)

    print('推測した結果の正解率', clf.score(test_matrix, test_ans))

    return clf, train_matrix, train_ans, test_matrix, test_ans, vectorizer

# 評価結果


def eval(clf, train_matrix, train_ans, test_matrix, test_ans, vectorizer):
    pred = clf.predict(test_matrix)
    cm = confusion_matrix(test_ans, pred, labels=[True, False])
    print(cm)

    pred = clf.predict(train_matrix)
    cm = confusion_matrix(train_ans, pred, labels=[True, False])
    print(cm)

    c = 0
    for col in np.argsort(clf.coef_[0])[::-1]:
        keys = [k for k, v in vectorizer.vocabulary_.items() if v == col]
        print("coef {0}: {1}".format(keys, clf.coef_[0][col]))  # パラメータ 上位重要度
        c += 1
        if c > 30:
            break


def main():
    # uniprot_sprot.dat
    train_aa, train_ans, test_aa, test_ans = ft_in("FT   DNA_BIND", sys.argv[1])
    clf, train_matrix, train_ans, test_matrix, test_ans, vectorizer = classification(train_aa, train_ans, test_aa, test_ans)
    eval(clf, train_matrix, train_ans, test_matrix, test_ans, vectorizer)


if __name__ == "__main__":
    main()

