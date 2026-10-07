# Batch analysis pipeline for tethered-cell videos.
# Combines object detection and frequency analysis; produces tethered-cells/results.csv.
import os
import cv2
import numpy as np
import pandas as pd
import pims
import scipy.signal
import matplotlib.pyplot as plt
from skimage.filters import threshold_multiotsu
from skimage.color import rgb2gray
from skimage import measure
from circle_fit import kmh

# MAIN ANALYSIS FUNCTION

def analyze_rotation(video_path, selected_region=None, min_size=25, max_size=100):

    # Get FPS
    video = cv2.VideoCapture(video_path)
    FPS = int(video.get(cv2.CAP_PROP_FPS))
    video.release()

    print(f"FPS: {FPS}")

    # Open Frames
    frames = pims.open(video_path)

    # Setup threshold
    test_img = frames[-1]
    test_gray = rgb2gray(test_img[:, :, :3])
    test_blur = cv2.GaussianBlur(test_gray, (7, 7), 0)

    thresholds = threshold_multiotsu(test_blur, classes=5)
    regions = np.digitize(test_blur, bins=thresholds)

    # Select region (only select region for the first video, same threshold region is used for each video...)
    if selected_region is None:

        selected = {"value": None}

        def onclick(event):
            if event.inaxes == ax[2]:
                x = int(event.xdata)
                y = int(event.ydata)

                rgn = regions[y, x]

                if rgn == 0:
                    print("Invalid region (0). Click again.")
                    return

                selected["value"] = rgn
                print(f"Selected region: {rgn}")
                plt.close()

        while selected["value"] is None:
            fig, ax = plt.subplots(1, 3, figsize=(12, 4))

            ax[0].imshow(test_img)
            ax[0].set_title("Original")

            ax[1].imshow(test_blur, cmap='gray')
            ax[1].set_title("Blurred")

            ax[2].imshow(regions, cmap='jet')
            ax[2].set_title("Click region (used for ALL videos)")

            for a in ax:
                a.axis("off")

            fig.canvas.mpl_connect('button_press_event', onclick)
            plt.tight_layout()
            plt.show()
            plt.close('all')

        rgn = selected["value"]

    else:
        rgn = selected_region
        print(f"Using saved region: {rgn}")

    # apply threshold
    tsh = thresholds[rgn - 1]
    print(f"Using threshold: {tsh:.3f}")

    # object detection
    img_properties = []
    frame_id = 0

    for img in frames:
        gscale = rgb2gray(img[:, :, :3])
        blur = cv2.GaussianBlur(gscale, (7, 7), 0)

        # detect DARK object
        binary = blur < tsh

        label = measure.label(binary)
        props = measure.regionprops(label)

        for obj in props:
            if min_size < obj.area < max_size:
                cpy, cpx = obj.centroid
                img_properties.append([
                    obj.area, cpx, cpy,
                    obj.major_axis_length,
                    obj.minor_axis_length,
                    frame_id
                ])
                break

        frame_id += 1

    df = pd.DataFrame(img_properties,
                      columns=['area', 'x', 'y', 'Majoraxis', 'Minoraxis', 'frame'])

    x = df["x"].to_numpy()
    y = df["y"].to_numpy()

    # center of rotation
    centroid_coords = df[["x", "y"]].to_numpy()
    windowsize = FPS * 10

    centre_X, centre_Y = [], []

    for i in range(len(centroid_coords)):
        if i <= len(centroid_coords) - windowsize:
            ctd_slice = centroid_coords[i:i + windowsize]
        else:
            ctd_slice = centroid_coords[-windowsize:]

        xc, yc, r, sigma = kmh(ctd_slice)
        centre_X.append(xc)
        centre_Y.append(yc)

    xc = np.array(centre_X)
    yc = np.array(centre_Y)

    # calculate frequency
    xcomp = x - xc
    ycomp = y - yc

    theta = np.unwrap(np.arctan2(ycomp, xcomp))
    freq = FPS * np.diff(theta) / (2 * np.pi)

    # filter
    freq_filt = scipy.signal.medfilt(freq, kernel_size=51)
    pos_freq = freq_filt[freq_filt > 0]
    neg_freq = freq_filt[freq_filt < 0]

    avg_pos_freq = np.mean(pos_freq) if len(pos_freq) > 0 else 0
    avg_neg_freq = np.mean(neg_freq) if len(neg_freq) > 0 else 0

    percent_positive = np.mean(freq_filt > 0) * 100
    avg_size = np.mean(df["Majoraxis"].to_numpy())

    return avg_pos_freq, avg_neg_freq, percent_positive, avg_size, rgn

# BATCH PROCESSING
def process_folder(folder_path, output_csv="results.csv"):

    results = []

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(".avi")]

    print(f"Found {len(files)} video(s)\n")

    selected_region = None  # persists across videos

    for i, file in enumerate(files, 1):
        video_path = os.path.join(folder_path, file)

        print(f"\n--- Processing ({i}/{len(files)}): {file} ---")

        try:
            avg_pos, avg_neg, pct_pos, size, selected_region = analyze_rotation(
                video_path,
                selected_region
            )

            results.append({
                "filename": file,
                "avg_positive_frequency": avg_pos,
                "avg_negative_frequency": avg_neg,
                "percent_time_positive": pct_pos,
                "object_size": size,
                "region_used": selected_region
            })

        except Exception as e:
            print(f"Error processing {file}: {e}")

            results.append({
                "filename": file,
                "avg_positive_frequency": None,
                "avg_negative_frequency": None,
                "percent_time_positive": None,
                "object_size": None,
                "region_used": selected_region
            })

    df = pd.DataFrame(results)

    output_path = os.path.join(folder_path, output_csv)
    df.to_csv(output_path, index=False)

    print(f"Results saved to: {output_path}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    folder = input("Enter folder path with AVI files: ")
    process_folder(folder)