"""Script to plot similarity distributions from log files."""
import json
import os
import glob
from datetime import datetime

import matplotlib.pyplot as plt
import seaborn as sns


def get_newest_similarity_log():
    """Get the path to the newest similarity log file.

    Returns:
        str: Path to the newest similarity log file.
    """
    log_dir = 'src/outputs/logs/similarity_logs/'

    # Get all JSON files in the similarity logs directory
    log_files = glob.glob(os.path.join(log_dir, 'similarity_log_*.json'))

    if not log_files:
        raise FileNotFoundError("No similarity log files found")

    # Extract timestamps from filenames and find the newest
    def get_timestamp_from_filename(filename):
        # Filename format: similarity_log_STRATEGY_YYYYMMDD_HHMMSS.json
        timestamp_str = os.path.basename(filename).split(
            '_')[-2] + os.path.basename(filename).split('_')[-1].replace('.json', '')
        return datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')

    # Sort files by timestamp in filename (newest first)
    newest_file = max(log_files, key=get_timestamp_from_filename)

    return newest_file


def plot_similarity_distribution(log_file):
    """Plot the distribution of similarity scores from a log file.

    Args:
        log_file (str): Path to the similarity log file.
    """
    # Load the similarity log
    with open(log_file, 'r', encoding='utf-8') as f:
        log_data = json.load(f)

    # Extract similarity scores
    similarities = [entry['similarity'] for entry in log_data]

    # Get strategy name from filename
    strategy_name = os.path.basename(log_file).split('_')[2]

    # Create a histogram
    plt.figure(figsize=(10, 6))
    sns.histplot(similarities, bins=50)
    plt.title(f'Distribution of Article Similarities ({strategy_name})')
    plt.xlabel('Similarity Score')
    plt.ylabel('Count')

    # Add statistics as text
    stats_text = (
        f'Mean: {sum(similarities)/len(similarities):.3f}\n'
        f'Min: {min(similarities):.3f}\n'
        f'Max: {max(similarities):.3f}\n'
        f'Count: {len(similarities)}'
    )
    plt.text(0.95, 0.95, stats_text,
             transform=plt.gca().transAxes,
             verticalalignment='top',
             horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Add runtime metadata in a discrete way
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    metadata_text = f'Generated: {current_time}\nSource: {os.path.basename(log_file)}'
    plt.text(0.02, 0.02, metadata_text,
             transform=plt.gca().transAxes,
             verticalalignment='bottom',
             horizontalalignment='left',
             fontsize=8,
             alpha=0.5)

    # Save the plot
    output_dir = os.path.dirname(log_file)
    output_filename = f'similarity_plot_{strategy_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    output_path = os.path.join(output_dir, output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")

    plt.show()


def main():
    """Main function to plot similarity distributions."""
    try:
        newest_log = get_newest_similarity_log()
        # newest_log = 'src/outputs/logs/similarity_logs/similarity_log_BERTSimilarity_20240321_143022.json'
        print(f"Loading similarity log: {newest_log}")
        plot_similarity_distribution(newest_log)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
