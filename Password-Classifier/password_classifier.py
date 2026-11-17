import argparse
import csv
import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    classification_report, confusion_matrix
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from scipy.sparse import hstack, csr_matrix


def save_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_data(folder, limit=0):
    passwords, labels = [], []
    files = sorted(Path(folder).glob("*.txt"))
    if not files:
        raise ValueError("No .txt files found")

    for file in files:
        count = 0
        with open(file, encoding="utf-8", errors="replace") as f:
            for line in f:
                p = line.rstrip("\r\n")
                if not p:
                    continue
                passwords.append(p)
                labels.append(file.stem)
                count += 1
                if limit and count >= limit:
                    break
        print(f"Loaded {file.stem}: {count:,}", flush=True)

    return passwords, labels


def split_dataset(passwords, labels, seed):
    # Keep each unique password in only one partition.
    # Exclude passwords with contradictory generator labels.
    owners = {}
    for p, g in zip(passwords, labels):
        owners.setdefault(p, set()).add(g)

    clean = [(p, next(iter(gs))) for p, gs in owners.items()
             if len(gs) == 1]

    print(f"Unique, unambiguous passwords: {len(clean):,}", flush=True)
    if not clean:
        raise ValueError("No usable passwords")

    names = sorted(set(g for _, g in clean))
    lookup = {g: i for i, g in enumerate(names)}
    x = np.array([p for p, _ in clean])
    y = np.array([lookup[g] for _, g in clean])

    a, x_test, b, y_test = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=seed
    )
    x_train, x_val, y_train, y_val = train_test_split(
        a, b, test_size=0.125, stratify=b, random_state=seed
    )
    return (x_train, x_val, x_test,
            y_train, y_val, y_test, names)


def evaluate(model_name, scores, y_test, names, output, seconds):
    scores = np.asarray(scores)
    ranks = np.argsort(scores, axis=1)[:, ::-1]
    pred = ranks[:, 0]
    n = len(names)

    def topk(y, r, k):
        return float(np.mean(np.any(
            r[:, :min(k, n)] == y[:, None], axis=1
        )))

    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, pred, labels=np.arange(n), zero_division=0
    )

    overall = {
        "model": model_name,
        "top1": topk(y_test, ranks, 1),
        "top3": topk(y_test, ranks, 3),
        "top5": topk(y_test, ranks, 5),
        "macro_precision": float(np.mean(precision)),
        "macro_recall": float(np.mean(recall)),
        "macro_f1": float(np.mean(f1)),
        "seconds": round(seconds, 2)
    }

    rows = []
    for i, name in enumerate(names):
        mask = y_test == i
        yi = y_test[mask]
        ri = ranks[mask]

        rows.append({
            "model": model_name,
            "generator": name,
            "support": int(support[i]),
            "top1": topk(yi, ri, 1) if len(yi) else 0,
            "top3": topk(yi, ri, 3) if len(yi) else 0,
            "top5": topk(yi, ri, 5) if len(yi) else 0,
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "macro_precision": overall["macro_precision"],
            "macro_recall": overall["macro_recall"],
            "macro_f1": overall["macro_f1"]
        })

    save_csv(output / f"{model_name}_per_generator.csv", rows)

    with open(output / f"{model_name}_metrics.json", "w") as f:
        json.dump(overall, f, indent=2)

    with open(output / f"{model_name}_report.txt", "w") as f:
        f.write(classification_report(
            y_test, pred, labels=np.arange(n),
            target_names=names, zero_division=0
        ))

    np.savetxt(
        output / f"{model_name}_confusion.csv",
        confusion_matrix(y_test, pred, labels=np.arange(n)),
        fmt="%d", delimiter=","
    )

    print(f"\n{model_name} RESULTS", flush=True)
    print(json.dumps(overall, indent=2), flush=True)
    return overall, rows


def structural(p):
    n = len(p)
    u = sum(c.isupper() for c in p)
    l = sum(c.islower() for c in p)
    d = sum(c.isdigit() for c in p)
    s = n - u - l - d
    return [n, u, l, d, s, len(set(p))]


def train_svm(xtr, ytr, xte, args):
    print("\n[SVM] Extracting character n-grams...", flush=True)
    start = time.time()

    vectorizer = TfidfVectorizer(
        analyzer="char", ngram_range=(1, 4),
        max_features=100000, min_df=2,
        dtype=np.float32
    )
    a = vectorizer.fit_transform(xtr)
    b = vectorizer.transform(xte)

    print("[SVM] Training LinearSVC...", flush=True)
    model = LinearSVC(C=1, dual=False, max_iter=3000)
    model.fit(a, ytr)
    scores = model.decision_function(b)

    joblib.dump((vectorizer, model), args.output / "svm.joblib")
    return scores, time.time() - start


def train_xgb(xtr, ytr, xval, yval, xte, args, n_classes):
    from xgboost import XGBClassifier

    print("\n[XGBoost] Extracting features...", flush=True)
    start = time.time()

    # Fixed character-position features, including identity and type.
    # Numeric character IDs impose an arbitrary ordering; this is a baseline.
    maxlen = max(map(len, xtr))
    chars = sorted(set("".join(xtr)))
    mapping = {c: i + 1 for i, c in enumerate(chars)}

    def encode(passwords):
        result = []
        for p in passwords:
            ids = [mapping.get(c, 0) for c in p]
            ids += [0] * (maxlen - len(ids))
            result.append(ids + structural(p))
        return np.asarray(result, dtype=np.float32)

    a, v, b = encode(xtr), encode(xval), encode(xte)

    model = XGBClassifier(
        n_estimators=args.trees,
        max_depth=args.depth,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        num_class=n_classes,
        tree_method="hist",
        n_jobs=-1,
        random_state=args.seed
    )

    print("[XGBoost] Training...", flush=True)
    model.fit(
        a, ytr,
        eval_set=[(v, yval)],
        verbose=25
    )

    scores = model.predict_proba(b)
    joblib.dump((model, mapping, maxlen),
                args.output / "xgb.joblib")
    return scores, time.time() - start


def train_cnn(xtr, ytr, xval, yval, xte, args, n_classes):
    import tensorflow as tf
    from tensorflow.keras import layers, Model

    print("\n[CNN] Preparing character sequences...", flush=True)
    start = time.time()

    chars = sorted(set("".join(xtr)))
    mapping = {c: i + 1 for i, c in enumerate(chars)}
    maxlen = max(map(len, xtr))

    def encode(passwords):
        arr = np.zeros((len(passwords), maxlen), dtype=np.int32)
        for i, p in enumerate(passwords):
            arr[i, :min(len(p), maxlen)] = [
                mapping.get(c, 0) for c in p[:maxlen]
            ]
        return arr

    a, v, b = encode(xtr), encode(xval), encode(xte)

    inputs = layers.Input(shape=(maxlen,))
    x = layers.Embedding(len(mapping) + 1, 64)(inputs)
    x = layers.Conv1D(128, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Conv1D(128, 5, padding="same", activation="relu")(x)
    x = layers.Bidirectional(
        layers.LSTM(128, return_sequences=True)
    )(x)

    attention = layers.MultiHeadAttention(
        num_heads=4, key_dim=32
    )(x, x)

    x = layers.Add()([x, attention])
    x = layers.LayerNormalization()(x)
    avg = layers.GlobalAveragePooling1D()(x)
    mx = layers.GlobalMaxPooling1D()(x)
    x = layers.Concatenate()([avg, mx])
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(n_classes, activation="softmax")(x)

    model = Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=5,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", patience=3, factor=0.5
        ),
        tf.keras.callbacks.CSVLogger(
            str(args.output / "cnn_training_history.csv")
        )
    ]

    print("[CNN] Training...", flush=True)
    history = model.fit(
        a, ytr,
        validation_data=(v, yval),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=2
    )

    model.save(args.output / "cnn_bilstm_attention.keras")
    with open(args.output / "cnn_mapping.json", "w") as f:
        json.dump({
            "mapping": mapping,
            "maxlen": maxlen
        }, f)

    scores = model.predict(
        b, batch_size=args.batch_size, verbose=1
    )
    return scores, time.time() - start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="generated_passwords")
    parser.add_argument("--output", type=Path,
                        default=Path("comparison_output"))
    parser.add_argument("--models", nargs="+",
                        choices=["cnn", "svm", "xgb"],
                        default=["cnn", "svm", "xgb"])
    parser.add_argument("--epochs", type=int, default=35)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--trees", type=int, default=300)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--max-per-class", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    passwords, labels = load_data(
        args.data, args.max_per_class
    )

    (xtr, xval, xte, ytr, yval, yte, names) = split_dataset(
        passwords, labels, args.seed
    )

    with open(args.output / "class_names.json", "w") as f:
        json.dump(names, f, indent=2)

    print(f"\nGenerators: {len(names)}")
    print(f"Train: {len(xtr):,}")
    print(f"Validation: {len(xval):,}")
    print(f"Test: {len(xte):,}", flush=True)

    all_results, all_generator_rows = [], []

    for name in args.models:
        if name == "svm":
            scores, seconds = train_svm(xtr, ytr, xte, args)
            label = "svm"
        elif name == "xgb":
            scores, seconds = train_xgb(
                xtr, ytr, xval, yval, xte, args, len(names)
            )
            label = "xgb"
        else:
            scores, seconds = train_cnn(
                xtr, ytr, xval, yval, xte, args, len(names)
            )
            label = "cnn_bilstm_attention"

        overall, rows = evaluate(
            label, scores, yte, names, args.output, seconds
        )
        all_results.append(overall)
        all_generator_rows.extend(rows)

        # Save immediately after each model finishes.
        save_csv(
            args.output / "model_comparison.csv",
            all_results
        )
        save_csv(
            args.output / "model_comparison_by_generator.csv",
            all_generator_rows
        )

    print("\nAll models finished.")
    print(f"Results saved to {args.output.resolve()}")


if __name__ == "__main__":
    main()
