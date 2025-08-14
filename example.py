# main.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
import datetime

# ---- AWS config from secrets ----
AWS_ACCESS_KEY_ID = st.secrets.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = st.secrets.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = st.secrets.get("AWS_REGION", "us-east-2")
S3_BUCKET_NAME = st.secrets.get("S3_BUCKET_NAME", "fob-dashboard-storage")


def get_s3_client():
    """Return a working S3 client and ensure the bucket exists / is accessible."""
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        st.error("AWS credentials missing in st.secrets.")
        return None

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
    # Ensure bucket exists (create if not found)
    try:
        s3.head_bucket(Bucket=S3_BUCKET_NAME)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchBucket"):
            try:
                if AWS_REGION == "us-east-1":
                    s3.create_bucket(Bucket=S3_BUCKET_NAME)
                else:
                    s3.create_bucket(
                        Bucket=S3_BUCKET_NAME,
                        CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
                    )
                st.info(f"Created bucket: {S3_BUCKET_NAME}")
            except ClientError as ce:
                st.error(f"Could not create bucket: {ce}")
                return None
        elif code == "403":
            st.error(f"Access denied to bucket '{S3_BUCKET_NAME}'. Check IAM policy.")
            return None
        else:
            st.error(f"S3 bucket error: {e}")
            return None
    return s3


def save_figure_to_project(fig, username: str, project_name: str, figure_name: str):
    """Upload matplotlib figure to S3 under the project folder; return (key, url)."""
    s3 = get_s3_client()
    if not s3:
        return None, None

    # Dump figure to bytes
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_project = "".join(c for c in project_name if c.isalnum() or c in (" ", "-", "_")).strip() or "Project"
    safe_name = "".join(c for c in figure_name if c.isalnum() or c in (" ", "-", "_")).strip() or "plot"

    key = f"user_data/{username}/projects/{safe_project}/figures/{safe_name}_{ts}.png"

    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=buf.getvalue(),
            ContentType="image/png",
            Metadata={
                "username": username,
                "project": safe_project,
                "figure_name": safe_name,
                "uploaded_at": ts,
            },
        )
        # Verify
        s3.head_object(Bucket=S3_BUCKET_NAME, Key=key)
    except ClientError as e:
        st.error(f"S3 upload failed: {e}")
        return None, None

    # Presigned URL (1 hour)
    try:
        url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET_NAME, "Key": key}, ExpiresIn=3600
        )
    except ClientError as e:
        st.warning(f"Could not generate presigned URL: {e}")
        url = None

    return key, url


def main():
    st.set_page_config(page_title="Minimal Project → Plot → Cloud", page_icon="☁️", layout="centered")
    st.title("Minimal: create a project → generate a plot → save to cloud")

    # --- Minimal "project" inputs ---
    username = st.text_input("Username", value="demo_user")
    project_name = st.text_input("Project name", value="DemoProject")
    figure_name = st.text_input("Figure name (optional)", value="minimal_plot")

    st.caption(
        f"S3 path preview: user_data/{username}/projects/{project_name}/figures/{figure_name}_<timestamp>.png"
    )

    # --- Generate a simple plot (example) ---
    x = np.arange(0, 10, 1)
    y = x ** 2
    fig, ax = plt.subplots()
    ax.plot(x, y, marker="o")
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Score")
    ax.set_title("Minimal Example Plot")
    st.pyplot(fig)

    # --- Save to cloud ---
    if st.button("Save plot to S3"):
        key, url = save_figure_to_project(fig, username=username, project_name=project_name, figure_name=figure_name)
        plt.close(fig)

        if key:
            st.success("✅ Uploaded to S3")
            st.code(key, language="text")
            if url:
                st.markdown(f"[Download (valid 1h)]({url})")
        else:
            st.error("Upload failed. Check secrets, IAM permissions, bucket region, and internet access.")

if __name__ == "__main__":
    main()
