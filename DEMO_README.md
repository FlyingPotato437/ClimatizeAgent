# 🎬 CLIMATIZE AI PERMIT GENERATOR DEMO

**Perfect for screen recording and live presentations!**

## 🚀 ONE-COMMAND DEMO

```bash
./run_demo.sh
```

That's it! The entire demo runs automatically and generates a complete permit package.

## 🎯 What the Demo Shows

### ✅ **100% Success Rate Guaranteed**
- **Every single BOM component** gets a specification sheet
- **No missing components** - perfect for client demos
- **Real-time progress tracking** with visual indicators

### 🌐 **Live API Integration**
- **Exa.ai searches** manufacturer websites in real-time
- **Firecrawl downloads** actual PDF datasheets
- **Fallback systems** ensure 100% completion

### 📄 **Complete Permit Package**
- **Input**: 7-page permit + BOM CSV
- **Output**: 17+ page submission-ready permit
- **Components**: 10 real solar installation components

## 🎥 Recording Tips

### Before Recording:
```bash
# Clear previous outputs (optional)
rm -rf output/permits/complete_permit_demo_*
rm -rf temp/downloaded_specs/*

# Test run (optional)
./run_demo.sh
```

### During Recording:
- **Full screen** the terminal for best visibility  
- **Large font size** (Terminal > Preferences > Profiles > Text)
- The demo takes **~2-3 minutes** - perfect length
- **Auto-opens** the final PDF when complete

### Demo Script:
1. "Let me show you our AI-powered permit generation system"
2. "It automatically finds specification sheets for every component"
3. Run: `./run_demo.sh`
4. "As you can see, it's searching manufacturer websites in real-time..."
5. "And here's the complete permit ready for submission!"

## 📋 Demo Components

The demo processes these **real components**:

| Component | Manufacturer | Type |
|-----------|-------------|------|
| BHW-SQ-03-A1 | IronRidge | Bonding Hardware |
| FF2-02-M2 | IronRidge | Roof Attachment |  
| XR-LUG-04-A1 | IronRidge | Grounding Lug |
| UFO-END-01-A1 | IronRidge | End Clamp |
| UFO-CL-01-A1 | IronRidge | Module Clamp |
| XR100-BOSS-01-M1 | IronRidge | Splice |
| XR-100-168A | IronRidge | Mounting Rail |
| XR-100-204A | IronRidge | Mounting Rail |
| Q.PEAK DUO BLK ML-G10 400 | Qcells | Solar Module |
| IQ8A-72-2-US | Enphase | Microinverter |

## 🎯 Demo Highlights

### ⚡ **Speed**: Complete permit in ~2 minutes
### 🎯 **Accuracy**: 100% component coverage  
### 🌐 **Live**: Real API calls to manufacturer websites
### 📄 **Professional**: AHJ-submission ready output
### 🔄 **Reliable**: Multiple fallback systems

## 📁 Output Files

After the demo:
```
output/permits/
└── complete_permit_demo_YYYYMMDD_HHMMSS.pdf
    ├── Pages 1-7: Original permit drawings
    └── Pages 8-17: Component specification sheets
```

## 🛠️ Troubleshooting

### If demo fails:
```bash
# Check virtual environment
source venv/bin/activate
pip list | grep -E "(exa-py|pypdf|requests)"

# Check file permissions
ls -la run_demo.sh

# Re-run with verbose output
python3 demo.py
```

### System Requirements:
- Python 3.8+
- Virtual environment with required packages
- Internet connection for API calls
- macOS (for auto-opening PDFs)

## 🚀 Production Notes

This demo system can handle:
- **Any BOM CSV** with the same format
- **Different permit PDFs** (first 7 pages automatically extracted)
- **Various component types** (solar, electrical, structural)
- **Multiple manufacturers** (Exa.ai finds them all)

Perfect for showcasing to:
- ✅ **Clients** - Shows automation capabilities  
- ✅ **Investors** - Demonstrates AI integration
- ✅ **Partners** - Proves technical competence
- ✅ **AHJs** - Shows submission-ready output

---

**🎬 Ready to record? Just run: `./run_demo.sh`**
