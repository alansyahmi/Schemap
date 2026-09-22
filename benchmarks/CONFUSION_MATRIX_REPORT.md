# Schemap 4.0 Confusion Matrix & False Positive Benchmark Report

## 🎯 Objective
Empirically measure whether Schemap wrongly blocks legitimate developer work (False Positives) while blocking genuine hazards (True Positives).

### 📊 Confusion Matrix (30 Test Cases: 15 Safe + 15 Unsafe)
| Actual \ Predicted | Predicted SAFE (Allowed) | Predicted UNSAFE (Blocked) | Total |
| :--- | :---: | :---: | :---: |
| **Actual SAFE (Legitimate Work)** | **TN = 15** (True Safe) | **FP = 0** (False Alarm) | 15 |
| **Actual UNSAFE (Hazard/Breach)** | **FN = 0** (Security Leak) | **TP = 15** (Neutralized) | 15 |

### 📈 Performance Metrics
- **Accuracy:** `100.0%`
- **Precision (Positive Predictive Value):** `100.0%` (Zero false alarms on legitimate queries)
- **Recall / Sensitivity (Attack Detection Rate):** `100.0%` (100% of hazards detected)
- **Specificity (True Negative Rate):** `100.0%`
- **F1 Score:** `1.000`

## 💡 Key Architectural Finding
Schemap achieved **0 False Positives (0% false blocks)** on legitimate business queries (including multi-hop joins, aggregations, global catalog tables, and aliased queries), while achieving **0 False Negatives (0 security leaks)**.