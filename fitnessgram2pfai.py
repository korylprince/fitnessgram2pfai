import argparse
import sys
from collections import defaultdict
from datetime import datetime
import re
import csv

pfai_headers = "School ID", "School Name", "Test Date", "Student DOB", "Student Grade", "Student Gender", "Height", "Weight", "Skinfold Tricep", "Skinfold Calf", "1 Mile Run (Minutes)", "1 Mile Run (Seconds)", "PACER Laps", "1 Mile Walk (Minutes)", "1 Mile Walk (Seconds)", "1 Mile Walk Heart Rate", "Curl Up", "Trunk Lift", "Push Up", "Modified Pull Up", "Flexed Arm Hang", "Back Saver Sit & Reach-Left", "Back Saver Sit & Reach-Right", "Shoulder Stretch-Left", "Shoulder Stretch-Right", "IsHispanicLatino", "IsAmericanIndianAlaskaNative", "IsAsian", "IsBlackAfricanAmerican", "IsNativeHawaiianOtherPacificIslander", "IsWhite"


# maps PFAI headers to Fitnessgram headers
field_map = {
    "School ID": "SchoolID",
    "School Name": "SchoolName",
    # "Test Date" is calculated from the latest TestEventEndDate field
    "Test Date": "TestDate",
    "Student DOB": "StudentDOB",
    "Student Grade": "Grade",
    "Student Gender": "Gender",
    # "Height" is calculated from the HeightFT and HeightIN fields
    "Height": "Height",
    "Weight": "Weight",
    "Skinfold Tricep": "TricepsSkinfold",
    "Skinfold Calf": "CalfSkinfold",
    "1 Mile Run (Minutes)": "OneMileRunMin",
    "1 Mile Run (Seconds)": "OneMileRunSec",
    # "PACER Laps" is calculated PACER15laps and PACER20laps fields
    "PACER Laps": "PACER Laps",
    "1 Mile Walk (Minutes)": "WalkTestMinutes",
    "1 Mile Walk (Seconds)": "WalkTestSeconds",
    "1 Mile Walk Heart Rate": "WalkTestHeartRate",
    "Curl Up": "Curlup",
    "Trunk Lift": "TrunkLift",
    "Push Up": "Pushup",
    "Modified Pull Up": "ModifiedPullup",
    "Flexed Arm Hang": "FlexedArmHang",
    "Back Saver Sit & Reach-Left": "SitandReachL",
    "Back Saver Sit & Reach-Right": "SitandReachR",
    "Shoulder Stretch-Left": "ShoulderStretchL",
    "Shoulder Stretch-Right": "ShoulderStretchR",
    # race/ethnicity fields are translated from Race and Ethnicity fields
    "IsHispanicLatino": "IsHispanicLatino",
    "IsAmericanIndianAlaskaNative": "IsAmericanIndianAlaskaNative",
    "IsAsian": "IsAsian",
    "IsBlackAfricanAmerican": "IsBlackAfricanAmerican",
    "IsNativeHawaiianOtherPacificIslander": "IsNativeHawaiianOtherPacificIslander",
    "IsWhite": "IsWhite"
}

def max_date(dates):
    return max([datetime.strptime(d.split(" ")[0], "%m/%d/%Y").date() for d in dates if d != ""]).strftime("%m/%d/%Y")


# Fitnessgram -> Reports -> Data Export -> FitnessGram Data Export
def read_fg(path, warn):
    with open(path, encoding="utf-16le") as f:
        r = csv.reader(f)
        header = [f.replace(" ", "") for f in next(r)]
        fitnessgram = [dict(zip(header, row)) for row in r]

    fMap = defaultdict(lambda:[])
    for f in fitnessgram:
        fMap[f["StudentID"]].append(f)

    for id, dicts in fMap.items():
        # merge duplicate student results
        final = dicts[0]
        for d in dicts[1:]:
            for k, v in d.items():
                if k not in final and v != "":
                    final[k] = v

        # parse school id
        try:
            final["SchoolID"] = final["SchoolID"].split("-")[1]
        except:
            if warn:
                print(f"WARN: Student ({id}): Unable to parse SchoolID \"{final['SchoolID']}\" to 9-digit code")

        # parse birth date
        try:
            final["StudentDOB"] = datetime.strptime(final["StudentDOB"].split(" ")[0], "%m/%d/%Y").strftime("%m/%d/%Y")
        except:
            if warn:
                print(f"WARN: Student ({id}): Unable to parse StudentDOB \"{final['StudentDOB']}\" to valid date")

        # parse test date
        final["TestDate"] = max_date([d["TestEventEndDate"] for d in dicts])

        # parse height
        final["Height"] = ""
        try:
            final["Height"] = str(int(final["HeightFT"]) * 12 + int(float(final["HeightIN"])))
        except:
            pass

        # parse weight
        try:
            final["Weight"] = str(int(float(final["Weight"])))
        except:
            pass

        # parse PACER
        final["PACER Laps"] = final["PACER15laps"] if final["PACER15laps"] != "" else final["PACER20laps"]

        # parse race/ethnicity
        final["IsHispanicLatino"] = "1" if final["Ethnicity"] == "Hispanic or Latino" else "0"
        final["IsAmericanIndianAlaskaNative"] = "1" if final["Race"] == "American Indian or Alaska Native" else "0"
        final["IsAsian"] = "1" if final["Race"] == "Asian" else "0"
        final["IsBlackAfricanAmerican"] = "1" if final["Race"] == "Black or African American" else "0"
        final["IsNativeHawaiianOtherPacificIslander"] = "1" if final["Race"] == "Native Hawaiian or Other Pacific Islander" else "0"
        final["IsWhite"] = "1" if final["Race"] == "White" else "0"

        exemptions = [k for k, v in final.items() if "HFZ" in k and v == "11"]

        # translate to PFAI fields
        final = {k: final[v] for k, v in field_map.items()}
        final["Exemptions"] = exemptions

        fMap[id] = final

    return fMap


def read_merge(path):
    with open(path) as f:
        r = csv.reader(f)
        header = next(r)
        return {d["Student ID"]: d for d in [dict(zip(header, row)) for row in r]}


def merge(fMap, mMap):
    for id, data in mMap.items():
        if id not in fMap:
            continue
        for k, v in data.items():
            if v != "":
                fMap[id][k] = v


def parse_date(d):
    try:
        return datetime.strptime(d, "%m/%d/%Y")
    except:
        return None


def validate(fMap, warn):
    for id, f in fMap.items():
        if re.match(r"^\d{9}$", f["School ID"]) is None and warn:
            print(f"WARN: Student ({id}): Invalid School ID \"{f['School ID']}\": Should be 9-digit code")
        if len(f["School Name"]) > 75 and warn:
            print(f"WARN: Student ({id}): Invalid School Name \"{f['School Name']}\": Max length is 75 characters")
        if parse_date(f["Test Date"]) is None and warn:
            print(f"WARN: Student ({id}): Invalid Test Date \"{f['Test Date']}\"")
        if parse_date(f["Student DOB"]) is None and warn:
            print(f"WARN: Student ({id}): Invalid Student DOB \"{f['Student DOB']}\"")
        if re.match("^(0?[3-9]|1[0-2])$", f["Student Grade"]) is None and warn:
            print(f"WARN: Student ({id}): Invalid Student Grade \"{f['Student Grade']}\": Should be in range 3-12")
        if re.match("^[mMfF]$", f["Student Gender"]) is None and warn:
            print(f"WARN: Student ({id}): Invalid Student Gender \"{f['Student Gender']}\": Should be \"M\" or \"F\"")

        # validate body composition
        valid_hw = re.match(r"^\d+$", f["Height"]) is not None and re.match(r"^\d+$", f["Weight"]) is not None
        valid_skin = re.match(r"^\d+$", f["Skinfold Tricep"]) is not None and re.match(r"^\d+$", f["Skinfold Calf"]) is not None
        if valid_hw:
            f["Skinfold Tricep"] = ""
            f["Skinfold Calf"] = ""
        elif valid_skin:
            f["Height"] = ""
            f["Weight"] = ""
        elif "BodyCompHFZ" not in f["Exemptions"] and "BMIHFZ" not in f["Exemptions"] and "PercentFatHFZ" not in f["Exemptions"] and warn:
            print(f"WARN: Student ({id}): Invalid Body Composition Test: Height (integer inches) and Weight (integer lbs) or Skinfold Tricep (integer) and Skinfold Calf (intger) must have data")

        # validate aerobic capacity
        valid_run = re.match(r"^\d+$", f["1 Mile Run (Minutes)"]) is not None and re.match(r"^[0-5]\d$", f["1 Mile Run (Seconds)"]) is not None
        valid_walk = re.match(r"^\d+$", f["1 Mile Walk (Minutes)"]) is not None and re.match(r"^[0-5]\d$", f["1 Mile Walk (Seconds)"]) is not None and re.match(r"^\d+$", f["1 Mile Walk Heart Rate"]) is not None
        if valid_run:
            f["PACER Laps"] = ""
            f["1 Mile Walk (Minutes)"] = ""
            f["1 Mile Walk (Seconds)"] = ""
            f["1 Mile Walk Heart Rate"] = ""
        elif re.match(r"^(\d|[1-9]\d|[1-3]\d{2})$", f["PACER Laps"]) is not None:
            f["1 Mile Run (Minutes)"] = ""
            f["1 Mile Run (Seconds)"] = ""
            f["1 Mile Walk (Minutes)"] = ""
            f["1 Mile Walk (Seconds)"] = ""
            f["1 Mile Walk Heart Rate"] = ""
        elif valid_walk:
            f["1 Mile Run (Minutes)"] = ""
            f["1 Mile Run (Seconds)"] = ""
            f["PACER Laps"] = ""
        elif "AerobicCapacityHFZ" not in f["Exemptions"] and warn:
            print(f"WARN: Student ({id}): Invalid Aerobic Capacity Test: 1 Mile Run (integer Minutes, Seconds), PACER Laps (0-300), or 1 Mile Walk (integer Minutes, Seconds, Heart Rate) must have data")

        # validate muscular strength and endurance
        # validate curl up
        if re.match(r"^(\d|[1-6]\d|7[0-5])$", f["Curl Up"]) is None and "CurlupHFZ" not in f["Exemptions"] and warn:
            print(f"WARN: Student ({id}): Invalid Curl Up \"{f['Curl Up']}\": Should be in range 0-75")

        # validate trunk lift
        if re.match(r"^(\d|1[0-2])$", f["Trunk Lift"]) is None and "TrunkLiftHFZ" not in f["Exemptions"] and warn:
            print(f"WARN: Student ({id}): Invalid Trunk Lift \"{f['Trunk Lift']}\": Should be in range 0-12")

        if re.match(r"^(\d|[1-9]\d)$", f["Push Up"]) is not None:
            f["Modified Pull Up"] = ""
            f["Flexed Arm Hang"] = ""
        elif re.match(r"^(\d|[1-9]\d|[1-9]\d{2})$", f["Modified Pull Up"]) is not None:
            f["Push Up"] = ""
            f["Flexed Arm Hang"] = ""
        elif re.match(r"^(\d|[1-9]\d|[1-9]\d{2})$", f["Flexed Arm Hang"]) is not None:
            f["Push Up"] = ""
            f["Modified Pull Up"] = ""
        elif "PushupHFZ" not in f["Exemptions"] and "ModifiedPullupHFZ" not in f["Exemptions"] and "FAHHFZ" not in f["Exemptions"] and warn:
            print(f"WARN: Student ({id}): Invalid Muscular Strength and Endurance Test: Push Up (integer 0-99), Modified Pull Up (integer 0-999), or Flexed Arm Hang (integer 0-999) must have data")

        #validate flexibility
        valid_bs = re.match(r"^(\d|1[0-2])$", f["Back Saver Sit & Reach-Left"]) is not None and re.match(r"^(\d|1[0-2])$", f["Back Saver Sit & Reach-Right"]) is not None
        valid_ss = re.match(r"^[1-2]$", f["Shoulder Stretch-Left"]) is not None and re.match(r"^[1-2]$", f["Shoulder Stretch-Right"]) is not None
        if valid_bs:
            f["Shoulder Stretch-Left"] = ""
            f["Shoulder Stretch-Right"] = ""
        elif valid_ss:
            f["Back Saver Sit & Reach-Left"] = ""
            f["Back Saver Sit & Reach-Right"] = ""
        elif "SitandReachHFZ" not in f["Exemptions"] and "ShoulderStretchHFZ" not in f["Exemptions"] and warn:
            print(f"WARN: Student ({id}): Invalid Flexility Test: Back Saver Sit & Reach-Left (integer 1-12) and Back Saver Sit & Reach-Right (integer 1-12) or Shoulder Stretch-Left (integer 1-2) and Shoulder Stretch-Right (intger 1-2) must have data")
        for race in ("IsHispanicLatino", "IsAmericanIndianAlaskaNative", "IsAsian", "IsBlackAfricanAmerican", "IsNativeHawaiianOtherPacificIslander", "IsWhite"):
            if re.match(r"^[0-1]?$", f[race]) is None and warn:
                print(f"WARN: Student ({id}): Invalid {race} ({f[race]}): Must be blank, 0, or 1")


def export(path, fMap):
    with open(path, "w") as f:
        w = csv.writer(f)
        w.writerow(pfai_headers)
        for _, f in fMap.items():
            w.writerow([f[h] for h in pfai_headers])


def main():
    parser = argparse.ArgumentParser(description="Convert Fitnessgram Export to PFAI Format")
    parser.add_argument("-in", dest="input", metavar="input.csv", type=str, required=True, help="Input \"Fitnessgram Data Export\" file path")
    parser.add_argument("-merge", metavar="merge.csv", type=str, help="Path to merge.csv")
    parser.add_argument("-warn", dest="warn", action="store_true", help="Log any validation issues to stdout")
    parser.add_argument("-out", metavar="output.csv", type=str, required=True, help="Output PFAI.csv file path")
    args = parser.parse_args()

    try:
        fMap = read_fg(args.input, args.warn)
    except Exception as e:
        print("Unable to open Fitnessgram Data Export:", e)
        sys.exit(-1)

    mMap = {}
    try:
        if args.merge:
            mMap = read_merge(args.merge)
    except Exception as e:
        print("Unable to open merge data:", e)
        sys.exit(-1)
    merge(fMap, mMap)

    validate(fMap, args.warn)

    try:
        export(args.out, fMap)
    except Exception as e:
        print("Unable to write output csv:", e)
        sys.exit(-1)


if __name__ == "__main__":
    main()
