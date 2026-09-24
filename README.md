# FM26 Squad Analysis & Moneyball Scouting

A Python/Jupyter Notebook workflow to parse, analyze, and visualize player data from Football Manager 2026.

---

## 🛠️ Prerequisites

1. **FM26 Player CSV Export Setup:**
   Follow the instructions on [FM Scout - FM26 Player CSV Export](https://www.fmscout.com/a-fm26-player-csv-export.html) to enable CSV export functionality in Football Manager 2026.

> [!IMPORTANT]
> **Game Language:** Ensure Football Manager 2026 is set to **English** when exporting CSV files. The analysis scripts rely strictly on English attribute names!

---

## 📁 Setup & Installation

### 1. Copy Views and Filters
Copy the provided views and filters from the repository's `fm_filters_and_views` folder to your local Football Manager directories:

* **Views:**  
  `Documents\Sports Interactive\Football Manager 26\views\`
* **Filters:**  
  `C:\Users\<YourUsername>\Documents\Sports Interactive\Football Manager 26\filters\`

---

### 2. Prepare Data Folders
Place your exported CSV files into the designated data directories (you can rename these folders as needed):

* **Own Squad CSV:** Place your own team's export in `data_1860_own_team` -> feel free to rename the folder structure to your own liking
* **Scouting / Transfer Targets CSV:** Place reference or target player exports in `data_1860` -> same here, feel free to rename the folder structure to your own liking

### 3. Install  Python packages

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

Open the respective Jupyter Notebooks, update the data folder path to point to your CSV files, and run all cells:

1. **`squad_overview.ipynb`**  
   Analyzes your squad's current roster, player profiles, and depth. -> make sure to adjust the folder names if changed
2. **`moneyball_transfer_targets.ipynb`**  
   Filters and scores potential scouting targets using custom Moneyball metrics. -> make sure to adjust the folder names if changed