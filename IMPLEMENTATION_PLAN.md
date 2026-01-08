# ImbLedger Enhancement Implementation Plan

## Overview
Comprehensive plan to add Entry tracking, reorganize metrics dashboard, and enhance performance analytics.

---

## Phase 1: Entry Field Addition ✅ COMPLETED
**Status:** Committed (84f7dd0)

### Completed Tasks:
- ✅ Added `entry` column to trades table (database migration)
- ✅ Updated INSERT statement in create_trade endpoint
- ✅ Added Entry input field to trade edit modal (HTML)
- ✅ Updated JavaScript to save/load entry field
- ✅ Positioned Entry between Confirmation and Model

---

## Phase 2: Entry Performance Statistics & API
**Status:** PENDING

### Backend Tasks (app.py):

#### 2.1 Add Entry Statistics Endpoint
```python
@app.route('/api/stats/entry')
def get_entry_stats():
    """Get performance statistics grouped by entry type"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            entry,
            COUNT(*) as count,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(pnl) as total_pnl,
            AVG(pnl) as avg_pnl,
            AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
            AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss
        FROM trades
        WHERE user_id = ? AND status = 'closed' AND entry IS NOT NULL AND entry != ''
        GROUP BY entry
        ORDER BY total_pnl DESC
    ''', (user_id,))

    results = cursor.fetchall()
    conn.close()

    stats = []
    for row in results:
        win_rate = (row['wins'] / row['count'] * 100) if row['count'] > 0 else 0
        stats.append({
            'name': row['entry'],
            'count': row['count'],
            'total_pnl': round(row['total_pnl'], 2),
            'win_rate': round(win_rate, 2),
            'avg_pnl': round(row['avg_pnl'], 2),
            'avg_win': round(row['avg_win'], 2) if row['avg_win'] else 0,
            'avg_loss': round(row['avg_loss'], 2) if row['avg_loss'] else 0
        })

    return jsonify(stats)
```

#### 2.2 Update Existing Statistics Endpoints
- Update `/api/stats/key_levels` (if exists) to use consistent format
- Update `/api/stats/confirmations` to use consistent format
- Update `/api/stats/models` to use consistent format

---

## Phase 3: Reorganize Performance Section Layout
**Status:** PENDING

### Frontend Tasks (single_page.html):

#### 3.1 Move Best Performers Below Performance by Hour

**Current Layout:**
```
- Metrics Dashboard (18 cards)
- PNL Chart + Time Heatmaps (2:1 ratio)
- Calendar
- Best Key Level (separate metric card)
- Best Model (separate metric card)
- Best Confirmation (separate metric card)
```

**New Layout:**
```
- Metrics Dashboard (reorganized, see Phase 5)
- PNL Chart + Time Heatmaps (2:1 ratio)
- Performance Category Cards (NEW - below heatmaps)
  - Performance by Key Level
  - Performance by Confirmation
  - Performance by Entry (NEW)
  - Performance by Model
- Calendar
```

#### 3.2 Create Performance Category Card Component

**HTML Structure:**
```html
<div class="performance-categories-section">
    <div class="performance-grid">
        <!-- Key Level Performance -->
        <div class="performance-card">
            <h4 class="performance-title">Performance by Key Level</h4>
            <div class="top-performer">
                <span class="performer-name" id="topKeyLevel">-</span>
                <span class="performer-pnl" id="topKeyLevelPnl">$0</span>
            </div>
            <select class="performance-dropdown" id="keyLevelDropdown">
                <option value="">Top 5 Key Levels</option>
            </select>
        </div>

        <!-- Confirmation Performance -->
        <div class="performance-card">
            <h4 class="performance-title">Performance by Confirmation</h4>
            <div class="top-performer">
                <span class="performer-name" id="topConfirmation">-</span>
                <span class="performer-pnl" id="topConfirmationPnl">$0</span>
            </div>
            <select class="performance-dropdown" id="confirmationDropdown">
                <option value="">Top 5 Confirmations</option>
            </select>
        </div>

        <!-- Entry Performance (NEW) -->
        <div class="performance-card">
            <h4 class="performance-title">Performance by Entry</h4>
            <div class="top-performer">
                <span class="performer-name" id="topEntry">-</span>
                <span class="performer-pnl" id="topEntryPnl">$0</span>
            </div>
            <select class="performance-dropdown" id="entryDropdown">
                <option value="">Top 5 Entries</option>
            </select>
        </div>

        <!-- Model Performance -->
        <div class="performance-card">
            <h4 class="performance-title">Performance by Model</h4>
            <div class="top-performer">
                <span class="performer-name" id="topModel">-</span>
                <span class="performer-pnl" id="topModelPnl">$0</span>
            </div>
            <select class="performance-dropdown" id="modelDropdown">
                <option value="">Top 5 Models</option>
            </select>
        </div>
    </div>
</div>
```

**CSS Styling:**
```css
.performance-categories-section {
    padding: 25px;
    background: #0b0b0b;
    border-bottom: 1px solid #333333;
}

.performance-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}

.performance-card {
    background: #111111;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
}

.performance-title {
    font-size: 0.85em;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 0 15px 0;
    font-weight: 500;
}

.top-performer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    background: rgba(255,255,255,0.03);
    border-radius: 8px;
    margin-bottom: 12px;
}

.performer-name {
    font-size: 1.1em;
    font-weight: 600;
    color: #fff;
}

.performer-pnl {
    font-size: 1.2em;
    font-weight: bold;
}

.performer-pnl.positive {
    color: #00ff88;
}

.performer-pnl.negative {
    color: #ff3366;
}

.performance-dropdown {
    width: 100%;
    padding: 10px 12px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    color: #ccc;
    font-size: 0.9em;
    cursor: pointer;
}

.performance-dropdown:hover {
    background: rgba(255,255,255,0.04);
    border-color: rgba(255,255,255,0.15);
}

.performance-dropdown option {
    background: #1a1a1a;
    color: #fff;
    padding: 8px;
}
```

#### 3.3 JavaScript Functions

```javascript
async function loadPerformanceCategories() {
    try {
        // Fetch all stats in parallel
        const [keyLevelStats, confirmationStats, entryStats, modelStats] = await Promise.all([
            fetch('/api/stats/key_levels').then(r => r.json()),
            fetch('/api/stats/confirmations').then(r => r.json()),
            fetch('/api/stats/entry').then(r => r.json()),
            fetch('/api/stats/models').then(r => r.json())
        ]);

        // Update Key Level
        updatePerformanceCard('keyLevel', keyLevelStats);

        // Update Confirmation
        updatePerformanceCard('confirmation', confirmationStats);

        // Update Entry
        updatePerformanceCard('entry', entryStats);

        // Update Model
        updatePerformanceCard('model', modelStats);

    } catch (error) {
        console.error('Error loading performance categories:', error);
    }
}

function updatePerformanceCard(category, stats) {
    if (!stats || stats.length === 0) {
        document.getElementById(`top${capitalize(category)}`).textContent = 'No data';
        document.getElementById(`top${capitalize(category)}Pnl`).textContent = '$0';
        return;
    }

    // Sort by total PnL descending
    stats.sort((a, b) => b.total_pnl - a.total_pnl);

    // Update top performer
    const topPerformer = stats[0];
    document.getElementById(`top${capitalize(category)}`).textContent = topPerformer.name;

    const pnlElement = document.getElementById(`top${capitalize(category)}Pnl`);
    pnlElement.textContent = `$${topPerformer.total_pnl.toFixed(0)}`;
    pnlElement.className = `performer-pnl ${topPerformer.total_pnl >= 0 ? 'positive' : 'negative'}`;

    // Populate dropdown with top 5
    const dropdown = document.getElementById(`${category}Dropdown`);
    dropdown.innerHTML = '<option value="">Top 5 ' + capitalize(category) + 's</option>';

    stats.slice(0, 5).forEach((stat, index) => {
        const option = document.createElement('option');
        option.value = stat.name;
        const pnlSign = stat.total_pnl >= 0 ? '+' : '';
        option.textContent = `${index + 1}. ${stat.name} (${pnlSign}$${stat.total_pnl.toFixed(0)} | ${stat.win_rate.toFixed(0)}% WR)`;
        dropdown.appendChild(option);
    });
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
```

---

## Phase 4: Add Sharpe Ratio to Metrics
**Status:** PENDING

### Backend Implementation:

#### 4.1 Calculate Sharpe Ratio
```python
@app.route('/api/stats/sharpe_ratio')
def get_sharpe_ratio():
    """Calculate Sharpe Ratio for trade performance"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT pnl
        FROM trades
        WHERE user_id = ? AND status = 'closed' AND pnl IS NOT NULL
        ORDER BY entry_time
    ''', (user_id,))

    pnls = [row['pnl'] for row in cursor.fetchall()]
    conn.close()

    if len(pnls) < 2:
        return jsonify({'sharpe_ratio': 0.0})

    # Calculate Sharpe Ratio
    import statistics
    mean_return = statistics.mean(pnls)
    std_dev = statistics.stdev(pnls)

    sharpe_ratio = (mean_return / std_dev) if std_dev > 0 else 0

    return jsonify({'sharpe_ratio': round(sharpe_ratio, 2)})
```

#### 4.2 Add to calculateStats() function
Update the existing stats calculation to include Sharpe ratio.

---

## Phase 5: Reorganize Metrics Dashboard (5 Priority Sizes)
**Status:** PENDING

### New Metrics Organization:

#### Priority 1 (Largest - 2 cards per row):
```css
.metric-card.priority-1 {
    grid-column: span 3; /* Takes half of 6-column grid */
    padding: 24px;
}
```
- **Balance**
- **Total P&L**

#### Priority 2 (Large - 3 cards per row):
```css
.metric-card.priority-2 {
    grid-column: span 2; /* Takes 1/3 of 6-column grid */
    padding: 20px;
}
```
- **Win Rate**
- **Profit Factor**
- **Expectancy**

#### Priority 3 (Medium - 3 cards per row):
```css
.metric-card.priority-3 {
    grid-column: span 2;
    padding: 18px;
}
```
- **Max Drawdown**
- **Largest Loss**
- **Sharpe Ratio** (NEW)

#### Priority 4 (Small - 4 cards per row):
```css
.metric-card.priority-4 {
    grid-column: span 1.5;
    padding: 16px;
}
```
- **Total Trades**
- **Avg Win**
- **Avg Loss**
- **Avg R:R**

#### Priority 5 (Smallest - 6 cards per row):
```css
.metric-card.priority-5 {
    grid-column: span 1;
    padding: 14px;
}
```
- **Win Streak**
- **Loss Streak**
- **Avg Hold Period**
- **Best Key Level**
- **Best Confirmation**
- **Best Entry** (NEW)
- **Best Model**

### Implementation:

```html
<div class="metrics-dashboard" id="metricsDashboard">
    <!-- Priority 1: Largest (2 cards) -->
    <div class="metric-card priority-1">
        <div class="metric-label">Balance</div>
        <div class="metric-value" id="accountBalance">$0</div>
    </div>
    <div class="metric-card priority-1">
        <div class="metric-label">Total P&L</div>
        <div class="metric-value" id="totalPnl">$0</div>
    </div>

    <!-- Priority 2: Large (3 cards) -->
    <div class="metric-card priority-2">
        <div class="metric-label">Win Rate</div>
        <div class="metric-value" id="winRateValue">0%</div>
        <div class="chart-container">
            <canvas id="winRateChart"></canvas>
        </div>
    </div>
    <div class="metric-card priority-2">
        <div class="metric-label">Profit Factor</div>
        <div class="metric-value" id="profitFactor">0.00</div>
    </div>
    <div class="metric-card priority-2">
        <div class="metric-label">Expectancy</div>
        <div class="metric-value" id="expectancy">$0</div>
    </div>

    <!-- Priority 3: Medium (3 cards) -->
    <div class="metric-card priority-3">
        <div class="metric-label">Max Drawdown</div>
        <div class="metric-value" id="maxDrawdown">$0</div>
        <div class="metric-sub" id="maxDrawdownPct">0%</div>
    </div>
    <div class="metric-card priority-3">
        <div class="metric-label">Largest Loss</div>
        <div class="metric-value negative" id="largestLoss">$0</div>
    </div>
    <div class="metric-card priority-3">
        <div class="metric-label">Sharpe Ratio</div>
        <div class="metric-value" id="sharpeRatio">0.00</div>
    </div>

    <!-- Priority 4: Small (4 cards) -->
    <div class="metric-card priority-4">
        <div class="metric-label">Total Trades</div>
        <div class="metric-value" id="totalTrades">0</div>
    </div>
    <div class="metric-card priority-4">
        <div class="metric-label">Avg Win</div>
        <div class="metric-value positive" id="avgWin">$0</div>
    </div>
    <div class="metric-card priority-4">
        <div class="metric-label">Avg Loss</div>
        <div class="metric-value negative" id="avgLoss">$0</div>
    </div>
    <div class="metric-card priority-4">
        <div class="metric-label">Avg R:R Ratio</div>
        <div class="metric-value" id="avgRRRatio">0:1</div>
    </div>

    <!-- Priority 5: Smallest (7 cards) -->
    <div class="metric-card priority-5">
        <div class="metric-label">Win Streak</div>
        <div class="metric-value" id="maxWinStreak">0</div>
    </div>
    <div class="metric-card priority-5">
        <div class="metric-label">Loss Streak</div>
        <div class="metric-value" id="maxLossStreak">0</div>
    </div>
    <div class="metric-card priority-5">
        <div class="metric-label">Avg Hold</div>
        <div class="metric-value" id="avgHoldPeriod">-</div>
    </div>
    <div class="metric-card priority-5">
        <div class="metric-label">Top Key</div>
        <div class="metric-value" id="bestKeyLevel" style="font-size: 0.75em;">-</div>
    </div>
    <div class="metric-card priority-5">
        <div class="metric-label">Top Conf</div>
        <div class="metric-value" id="bestConfirmation" style="font-size: 0.75em;">-</div>
    </div>
    <div class="metric-card priority-5">
        <div class="metric-label">Top Entry</div>
        <div class="metric-value" id="bestEntry" style="font-size: 0.75em;">-</div>
    </div>
    <div class="metric-card priority-5">
        <div class="metric-label">Top Model</div>
        <div class="metric-value" id="bestModel" style="font-size: 0.75em;">-</div>
    </div>
</div>
```

---

## Implementation Order Summary:

### Step 1: Backend APIs (30 mins)
- Add `/api/stats/entry` endpoint
- Add `/api/stats/sharpe_ratio` endpoint
- Update calculateStats() to include Sharpe ratio

### Step 2: Performance Categories Section (45 mins)
- Add HTML structure for 4 performance cards
- Add CSS styling for performance grid
- Implement loadPerformanceCategories() JavaScript
- Position below time heatmaps

### Step 3: Metrics Dashboard Reorganization (1 hour)
- Add CSS for 5 priority levels (priority-1 through priority-5)
- Reorganize HTML with new card structure
- Update grid to handle different column spans
- Add Sharpe Ratio metric card
- Add Best Entry metric card

### Step 4: Testing & Polish (30 mins)
- Test Entry field saving/loading
- Test all performance dropdowns
- Verify Sharpe ratio calculation
- Check responsive layout at different screen sizes
- Create final backup

---

## Total Estimated Time: 3-4 hours

## Files to Modify:
1. `app.py` - Backend APIs and Sharpe ratio calculation
2. `templates/single_page.html` - All frontend changes
3. No database migrations needed (entry column already added)

---

## Color Scheme for Entry Types:
```css
/* Entry-specific colors (similar to Key Level colors) */
.entry-limit { color: #00d4ff; } /* Cyan */
.entry-market { color: #ff8c00; } /* Orange */
.entry-stop { color: #9d4edd; } /* Purple */
```

---

## Next Steps:
1. Review this plan
2. Implement Phase 2 (Entry Statistics API)
3. Implement Phase 3 (Performance Categories)
4. Implement Phase 4 (Sharpe Ratio)
5. Implement Phase 5 (Metrics Reorganization)
6. Test & deploy

---

*Plan created: January 8, 2026*
*Implementation: Phased approach for manageable changes*
