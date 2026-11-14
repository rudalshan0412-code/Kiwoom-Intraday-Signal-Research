from __future__ import annotations

import argparse
import json

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

KST = ZoneInfo(
    "Asia/Seoul"
)


def summarize_head(
    frame: pd.DataFrame,
    head: str,
) -> dict:

    labels = pd.to_numeric(
        frame[
            f"label_{head}"
        ],
        errors="coerce",
    )

    weights = (
        pd.to_numeric(
            frame[
                f"weight_{head}"
            ],
            errors="coerce",
        )
        .fillna(
            0.0
        )
    )

    valid = (
        labels.notna()
        & (
            weights
            > 0
        )
    )

    labels = labels[
        valid
    ]

    weights = weights[
        valid
    ]

    positives = int(
        (
            labels
            >= 0.5
        ).sum()
    )

    negatives = int(
        (
            labels
            < 0.5
        ).sum()
    )

    weight_sum = float(
        weights.sum()
    )

    if weight_sum > 0:

        positive_rate = float(
            (
                (
                    labels
                    >= 0.5
                ).astype(
                    float
                )
                * weights
            ).sum()
            / weight_sum
        )

    else:

        positive_rate = None

    return {
        "rows":
            int(
                len(
                    labels
                )
            ),

        "positive":
            positives,

        "negative":
            negatives,

        "weight_sum":
            weight_sum,

        "positive_rate":
            positive_rate,
    }


def summarize_split(
    frame: pd.DataFrame,
) -> dict:

    return {
        "rows":
            int(
                len(
                    frame
                )
            ),

        "codes":
            int(
                frame[
                    "code"
                ].nunique()
            )
            if len(
                frame
            )
            else 0,

        "dates":
            sorted(
                {
                    value.isoformat()
                    for value
                    in frame[
                        "_date"
                    ]
                }
            )
            if len(
                frame
            )
            else [],

        "heads":
            {
                head:
                    summarize_head(
                        frame,
                        head,
                    )
                for head in (
                    "A",
                    "B",
                    "C",
                    "D",
                )
            },
    }


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--through-week",
        required=True,
    )

    parser.add_argument(
        "--validation-days",
        type=int,
        default=1,
    )

    args = parser.parse_args()

    if args.validation_days < 1:

        raise RuntimeError(
            "validation-days는 1 이상이어야 합니다."
        )

    cumulative_dir = (
        ROOT
        / "data"
        / "ml"
        / "cumulative"
        / args.through_week
    )

    source = (
        cumulative_dir
        / "intraday_labeled_cumulative.csv.gz"
    )

    if not source.exists():

        raise FileNotFoundError(
            source
        )

    frame = pd.read_csv(
        source,
        compression="gzip",
        dtype={
            "code":
                str,
        },
    )

    frame[
        "_timestamp"
    ] = pd.to_datetime(
        frame[
            "sample_time"
        ],
        errors="coerce",
    )

    if frame[
        "_timestamp"
    ].isna().any():

        raise RuntimeError(
            "sample_time 변환 실패 row 존재"
        )

    frame[
        "_date"
    ] = (
        frame[
            "_timestamp"
        ].dt.date
    )

    frame = (
        frame.sort_values(
            [
                "_timestamp",
                "code",
                "signal_id",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    dates = sorted(
        frame[
            "_date"
        ].unique()
    )

    output_dir = (
        ROOT
        / "data"
        / "ml"
        / "walk_forward"
        / args.through_week
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest_path = (
        output_dir
        / "split_manifest.json"
    )

    required_days = (
        args.validation_days
        + 1
    )

    print("=" * 80)
    print("WALK-FORWARD DATASET SPLIT")
    print("=" * 80)

    print(
        "[SOURCE]",
        source,
    )

    print(
        "[TRADING DAYS]",
        len(
            dates
        ),
    )

    print(
        "[DATES]",
        [
            value.isoformat()
            for value in dates
        ],
    )

    if len(
        dates
    ) < required_days:

        manifest = {
            "generated_at":
                datetime.now(
                    KST
                ).isoformat(
                    timespec="seconds"
                ),

            "through_week":
                args.through_week,

            "status":
                "NOT_READY",

            "reason":
                "NOT_ENOUGH_TRADING_DAYS",

            "trading_days":
                len(
                    dates
                ),

            "required_minimum_days":
                required_days,

            "validation_days":
                args.validation_days,
        }

        manifest_path.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        print()
        print(
            "[STATUS] NOT_READY"
        )

        print(
            "[REASON] "
            "NOT_ENOUGH_TRADING_DAYS"
        )

        print(
            "[TRAINING EXECUTED] False"
        )

        print(
            "[RUNTIME CHANGED] False"
        )

        return

    validation_dates = set(
        dates[
            -args.validation_days:
        ]
    )

    train = frame[
        ~frame[
            "_date"
        ].isin(
            validation_dates
        )
    ].copy()

    validation = frame[
        frame[
            "_date"
        ].isin(
            validation_dates
        )
    ].copy()

    if train.empty:

        raise RuntimeError(
            "Train dataset이 비었습니다."
        )

    if validation.empty:

        raise RuntimeError(
            "Validation dataset이 비었습니다."
        )

    train_max_time = (
        train[
            "_timestamp"
        ].max()
    )

    validation_min_time = (
        validation[
            "_timestamp"
        ].min()
    )

    if not (
        train_max_time
        < validation_min_time
    ):

        raise RuntimeError(
            "Walk-forward 시간 순서 위반"
        )

    train_summary = (
        summarize_split(
            train
        )
    )

    validation_summary = (
        summarize_split(
            validation
        )
    )

    drop_columns = (
        "_timestamp",
        "_date",
    )

    train_output = (
        output_dir
        / "train.csv.gz"
    )

    validation_output = (
        output_dir
        / "validation.csv.gz"
    )

    train.drop(
        columns=list(
            drop_columns
        )
    ).to_csv(
        train_output,
        index=False,
        compression="gzip",
        encoding="utf-8",
    )

    validation.drop(
        columns=list(
            drop_columns
        )
    ).to_csv(
        validation_output,
        index=False,
        compression="gzip",
        encoding="utf-8",
    )

    manifest = {
        "generated_at":
            datetime.now(
                KST
            ).isoformat(
                timespec="seconds"
            ),

        "through_week":
            args.through_week,

        "status":
            "READY",

        "split_method":
            "FULL_TRADING_DAY_WALK_FORWARD",

        "validation_days":
            args.validation_days,

        "train_end":
            train_max_time.isoformat(),

        "validation_start":
            validation_min_time.isoformat(),

        "train":
            train_summary,

        "validation":
            validation_summary,

        "files":
            {
                "train":
                    str(
                        train_output
                    ),

                "validation":
                    str(
                        validation_output
                    ),
            },
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "[STATUS] READY"
    )

    print(
        "[TRAIN ROWS]",
        len(
            train
        ),
    )

    print(
        "[VALIDATION ROWS]",
        len(
            validation
        ),
    )

    print(
        "[TRAIN END]",
        train_max_time,
    )

    print(
        "[VALIDATION START]",
        validation_min_time,
    )

    print()

    for head in (
        "A",
        "B",
        "C",
        "D",
    ):

        print(
            f"[TRAIN {head}]",
            train_summary[
                "heads"
            ][head],
        )

        print(
            f"[VALID {head}]",
            validation_summary[
                "heads"
            ][head],
        )

    print()
    print(
        "[TRAINING EXECUTED] False"
    )

    print(
        "[RUNTIME CHANGED] False"
    )

    print(
        "[RESULT] Walk-forward Split 완료"
    )


if __name__ == "__main__":
    main()
