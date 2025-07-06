# Catch the Healthy Food Game

A fun Pygame-based game where you catch healthy food and throw it at customers while avoiding unhealthy food and fireballs!

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Option 1: Using Virtual Environment (Recommended)

1. **Clone or download this project** to your local machine

2. **Open a terminal/command prompt** in the project directory

3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: Direct Installation (Not Recommended)

If you prefer not to use a virtual environment, you can install dependencies directly:
```bash
pip install -r requirements.txt
```

## Running the Game

1. **Make sure your virtual environment is activated** (if using Option 1)

2. **Run the game:**
   ```bash
   python game.py
   ```

## Game Controls

- **Arrow Keys (← →)**: Move left and right
- **X**: Jump
- **Z**: Throw stacked healthy food
- **ESC**: Return to menu (in submenus)

## Game Features

- **Main Menu**: Play, Instructions, About, Leaderboard, Quit
- **About Page**: Shows data analysis and linear regression results
- **Leaderboard**: Saves and displays top 5 scores
- **Animated GIFs**: Fun animations on menu and leaderboard pages
- **Background Music**: Different music for menu and gameplay
- **Responsive Design**: Adapts to your screen resolution

## File Structure

Make sure you have all these files in your project directory:
```
summer project/
├── game.py                    # Main game file
├── classes.py                 # Game classes
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── Nutrition_Value_Dataset.csv # Food data
├── data_plot_high_res.png     # Data visualization
├── game_active.mp3           # Game music
├── silly_menu.mp3            # Menu music
└── new_sprites/              # Game sprites and GIFs
    ├── spr_tenna_dance_cabbage.gif
    ├── spr_tenna_dance_cane.gif
    └── [other sprite files...]
```

## Troubleshooting

- **"pygame module not found"**: Make sure you've installed the requirements
- **"PIL module not found"**: Install Pillow: `pip install Pillow`
- **Music not playing**: Check that the .mp3 files are in the correct location
- **GIFs not animating**: Ensure the GIF files are in the `new_sprites` folder

## Requirements

- pygame==2.6.1
- Pillow==10.4.0
- scikit-learn==1.4.0
- pandas==2.2.0
- numpy==1.26.4

## Credits

Created as a summer project combining game development with data analysis concepts.
