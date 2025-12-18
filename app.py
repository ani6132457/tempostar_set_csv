import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="SKU 並び替えツール", layout="wide")

st.title("SKU 並び替えツール（VBA → Web/Python）")

st.markdown("""
- 親貼り付け：SKUコード一覧（1列目にSKU）
- 子貼り付け：照合用SKU一覧（1列目にSKU）
- 出力：Sheet3相当（セット商品区分 / SKUコード / セット個数）
""")

# =========
# UI
# =========
mode = st.radio(
    "処理モード",
    ["通常版（ama- と _ を削除して照合）", "cp版（_cp を削除して照合）"],
    horizontal=True
)

col1, col2 = st.columns(2)
with col1:
    parent_file = st.file_uploader("親貼り付け（CSV / Excel）", type=["csv", "xlsx"])
with col2:
    child_file = st.file_uploader("子貼り付け（CSV / Excel）", type=["csv", "xlsx"])

encoding = st.selectbox("CSV文字コード（CSVのとき）", ["cp932", "utf-8-sig", "utf-8"], index=0)

# =========
# helpers
# =========
def read_table(uploaded, encoding: str) -> pd.DataFrame:
    if uploaded is None:
        return None
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded, encoding=encoding)
    else:
        return pd.read_excel(uploaded)

def normalize_sku(sku1: str, mode: str) -> str:
    if sku1 is None:
        return ""
    sku1 = str(sku1).strip()
    if mode.startswith("通常版"):
        # ama- と _ を削除
        sku2 = sku1.replace("ama-", "").replace("_", "")
        return sku2
    else:
        # _cp を削除
        sku2 = sku1.replace("_cp", "")
        return sku2

# =========
# run
# =========
if parent_file and child_file:
    parent_df = read_table(parent_file, encoding)
    child_df = read_table(child_file, encoding)

    if parent_df is None or child_df is None:
        st.error("ファイルの読み込みに失敗しました。")
        st.stop()

    # 1列目をSKU列として扱う（VBAと同じ）
    parent_skus = parent_df.iloc[:, 0].astype(str).fillna("").str.strip()
    child_skus = set(child_df.iloc[:, 0].astype(str).fillna("").str.strip().tolist())

    out_rows = []
    for sku1 in parent_skus:
        if not sku1:
            continue

        sku2 = normalize_sku(sku1, mode)

        if sku2 in child_skus:
            # VBAの出力と同じ：1行目(区分=1, sku1)、2行目(区分=2, sku2, 個数=1)
            out_rows.append({"セット商品区分": 1, "SKUコード": sku1, "セット個数": ""})
            out_rows.append({"セット商品区分": 2, "SKUコード": sku2, "セット個数": 1})

    out_df = pd.DataFrame(out_rows, columns=["セット商品区分", "SKUコード", "セット個数"])

    st.subheader("結果プレビュー（Sheet3相当）")
    st.dataframe(out_df, use_container_width=True, height=520)

    # ダウンロード（CSV）
    csv_buf = io.StringIO()
    out_df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
    st.download_button(
        label="結果をCSVでダウンロード（UTF-8-SIG）",
        data=csv_buf.getvalue().encode("utf-8-sig"),
        file_name="sheet3_output.csv",
        mime="text/csv",
    )
else:
    st.info("親貼り付け・子貼り付けのファイルを両方アップロードしてください。")
