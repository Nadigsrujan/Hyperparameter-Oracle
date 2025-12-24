# 🚀 Quick Start Guide

## **Get Your Hyperparameter Oracle Running in 3 Minutes!**

---

## Option 1: Super Quick Start (Windows) ⚡

### Just double-click this file:

```
run.bat
```

That's it! The script will:
- ✅ Check Python installation
- ✅ Install dependencies automatically
- ✅ Compile C code if needed
- ✅ Start the server
- ✅ Open your browser to the dashboard

**Dashboard will open at:** `http://localhost:5000`

---

## Option 2: Manual Start 🔧

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Start the Server

```bash
cd src\python
python api_server.py
```

### Step 3: Open Browser

Navigate to: `http://localhost:5000`

---

## How to Use the Dashboard 🖥️

### 1. **Initialize the Oracle**

- Select a dataset (Iris, Wine, or Digits)
- Set max iterations (50-200 recommended)
- Click **"Initialize Oracle"**

### 2. **Start Optimization**

- Click **"Start Optimization"**
- Watch the real-time charts update!

### 3. **Monitor Progress**

You'll see:
- **Accuracy convergence** over iterations
- **Hyperparameter space** exploration (2D scatter)
- **DSA layer metrics** (all 12 data structures in action)
- **Best configuration** found so far
- **Live experiment log**

### 4. **Run Comparison**

- Click **"Run Comparison"**
- System benchmarks against:
  - Random Search
  - Grid Search
  - Bayesian Optimization
- Results shown in charts and table

---

## What You Should See 📊

### Dashboard Features:

1. **Header Stats**
   - Unique Configs Explored
   - Best Accuracy Achieved
   - Current Iteration / Max Iterations

2. **Control Panel**
   - Dataset selection
   - Iteration settings
   - Start/Stop controls
   - Comparison trigger

3. **Real-Time Charts**
   - Accuracy over time (line chart)
   - Hyperparameter space (scatter plot with color-coded accuracy)

4. **DSA Insights**
   - All 12 data structures shown as active
   - Their roles in the system

5. **Best Configuration Display**
   - C (Regularization parameter)
   - Gamma (Kernel parameter)
   - Achieved accuracy

6. **Experiment Log**
   - Real-time console-style output
   - Shows every decision made

---

## Example Output 📈

```
[Python] Loading Dataset (Iris)...
[Python] Starting Optimization Loop (50 iterations)...
--------------------------------------------------------
Iter  | Acc      | C        | Gamma    | DSA Stats
--------------------------------------------------------
1     | 0.9667   | 45.2341  | 0.3421   | Unique: 1
2     | 0.9733   | 52.1123  | 0.2891   | Unique: 2
3     | 0.9800   | 48.5677  | 0.3156   | Unique: 3
...
```

---

## Troubleshooting 🔍

### ❌ "Module not found: flask"

**Solution:**
```bash
pip install -r requirements.txt
```

### ❌ "oracle.dll not found"

**Solution:**
```bash
gcc -shared -o build\oracle.dll -fPIC src\c\*.c -Iinclude
```

### ❌ "Port 5000 already in use"

**Solution:**
1. Stop any process using port 5000
2. Or edit `api_server.py` and change the port:
   ```python
   app.run(debug=True, port=5001, host='0.0.0.0')
   ```

### ❌ Browser doesn't open automatically

**Solution:**
Manually navigate to: `http://localhost:5000`

---

## Testing the System ✅

### Quick Test (CLI Mode):

```bash
cd src\python
python main.py
```

This runs a quick 50-iteration test in the console.

### Full Test (Web Dashboard):

1. Start server: `python api_server.py`
2. Open: `http://localhost:5000`
3. Initialize with Iris dataset
4. Run 30 iterations
5. Check results

**Expected Result:**
- Accuracy should reach **0.96-0.98** within 20-30 iterations
- Should be faster than Random/Grid Search
- All charts should update in real-time

---

## What Makes This Special? ✨

Unlike traditional AutoML tools, this system:

1. **Explainable** - You can see exactly WHY each hyperparameter was chosen
2. **Educational** - Shows DSA in action on real problems
3. **Efficient** - Converges faster by learning from every trial
4. **Visual** - Beautiful real-time dashboard
5. **Comparative** - Built-in benchmarking against other methods

---

## Next Steps 👉

Once you have it running:

1. ✅ Try different datasets (Iris → Wine → Digits)
2. ✅ Experiment with iteration counts
3. ✅ Run the comparison to see performance gains
4. ✅ Check the experiment log to understand decisions
5. ✅ Read `DOCUMENTATION.md` for deep technical details

---

## File Structure Reference 📁

```
hyperparameter_oracle/
│
├── run.bat              ← DOUBLE-CLICK THIS!
├── README.md            ← General overview
├── QUICK_START.md       ← This file
├── DOCUMENTATION.md     ← Full technical docs
│
├── src/
│   ├── c/               ← DSA implementation
│   └── python/          ← ML + API
│
└── frontend/            ← Web dashboard
```

---

## Support 💬

**Having issues?**

1. Check `DOCUMENTATION.md` Section 10 (How to Use)
2. Verify Python 3.8+ is installed: `python --version`
3. Ensure all dependencies installed: `pip list`
4. Check the Flask console for error messages

---

## Ready? Let's Go! 🎯

```bash
# Just run this:
.\run.bat

# Or manually:
cd src\python
python api_server.py

# Then open:
# http://localhost:5000
```

---

**Have fun exploring DSA-driven hyperparameter optimization! 🚀**
