from utils.utils import sanitize_filename
import os

def save_competition_data(competition_data, competition_name):
    """Save competition data to a text file"""
    try:
        # Sanitize the competition name for the filename
        safe_name = sanitize_filename(competition_name)
        filepath = f"scrape_outputs/scrape_output-{safe_name}.txt"
        
        # Create scrape_outputs directory if it doesn't exist
        os.makedirs("scrape_outputs", exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(competition_data)
        return filepath
    except Exception as e:
        print(f"Error saving competition data: {e}")
        return None 