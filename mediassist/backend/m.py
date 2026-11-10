import csv

with open("evaluation.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

actual = [row["actual"].strip() for row in rows]
predicted = [row["predicted"].strip() for row in rows]

if not rows:
    raise SystemExit("The CSV has no evaluation rows.")

labels = sorted(set(actual) | set(predicted))
accuracy = sum(a == p for a, p in zip(actual, predicted)) / len(rows)

print(f"Accuracy: {accuracy:.1%}")
print("\nPer-class metrics:")

precisions, recalls, f1_scores = [], [], []

for label in labels:
    tp = sum(a == label and p == label for a, p in zip(actual, predicted))
    fp = sum(a != label and p == label for a, p in zip(actual, predicted))
    fn = sum(a == label and p != label for a, p in zip(actual, predicted))

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    precisions.append(precision)
    recalls.append(recall)
    f1_scores.append(f1)

    print(
        f"{label}: precision={precision:.1%}, "
        f"recall={recall:.1%}, F1={f1:.1%}"
    )

print(f"\nMacro precision: {sum(precisions) / len(labels):.1%}")
print(f"Macro recall:    {sum(recalls) / len(labels):.1%}")
print(f"Macro F1:        {sum(f1_scores) / len(labels):.1%}")
