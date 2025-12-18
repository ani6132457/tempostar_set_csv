import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="SKU 並び替えツール（貼り付け版）", layout="wide")
st.title("SKU 並び替えツール（貼り付け入力版）")

mode = st.radio(
    "処理モード",
    ["通常版（ama- と _ を削除して照合）", "cp版（_cp を削除して照合）"],
    horizontal=True
)

st.caption("ExcelからA列をコピーして、そのまま貼り付けOK（改行 / タブ / カンマを自動判定）")

c1, c2 = st.columns(2)
with c1:
    parent_text = st.text_area("親貼り付け（SKU一覧）", height=320, placeholder="例:\nama-7986600_setX11Y11\nama-7986601_setX11Y12\n...")
with c2:
    child_text = st.text_area("子貼り付け（照合用SKU一覧）", height=320, placeholder="例:\n7986600setX11Y11\n7986601setX11Y12\n...")

btn = st.button("実行", type="primary")

def extract_first_column_values(text: str) -> list[str]:
    """
    Excelから貼り付けたテキストを想定し、行ごとに「1列目だけ」を取り出す。
    区切り：タブ / カンマ / 複数スペース に対応（最初に見つかった区切りでsplit）
    """
    if not text:
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() != ""]
    out = []
    for ln in lines:
        # まずタブ優先（Excelコピーはほぼタブ）
        if "\t" in ln:
            first = ln.split("\t")[0].strip()
        # 次にカンマ（CSV貼り付けっぽい場合）
        elif "," in ln:
            first = ln.split(",")[0].strip()
        else:
            # スペースが混ざっていても、先頭トークンをSKUとみなす
            first = re.split(r"\s+", ln, maxsplit=1)[0].strip()
        if first:
            out.append(first)
    return out

def normalize_sku(sku1: str, mode: str) -> str:
    sku1 = str(sku1).strip()
    if mode.startswith("通常版"):
        return sku1.replace("ama-", "").replace("_", "")
    else:
        return sku1.replace("_cp", "")

if btn:
    parent_skus = extract_first_column_values(parent_text)
    child_skus_list = extract_first_column_values(child_text)
    child_skus = set(child_skus_list)

    if not parent_skus:
        st.error("親貼り付けが空です。")
        st.stop()
    if not child_skus:
        st.error("子貼り付けが空です。")
        st.stop()

    out_rows = []
    for sku1 in parent_skus:
        sku2 = normalize_sku(sku1, mode)
        if sku2 in child_skus:
            out_rows.append({"セット商品区分": 1, "SKUコード": sku1, "セット個数": ""})
            out_rows.append({"セット商品区分": 2, "SKUコード": sku2, "セット個数": 1})

    out_df = pd.DataFrame(out_rows, columns=["セット商品区分", "SKUコード", "セット個数"])

    st.subheader("結果（Sheet3相当）")
    st.dataframe(out_df, use_container_width=True, height=520)

    # そのままコピーできるTSV（Excelに貼りやすい）
    st.subheader("コピー用（Excel貼り付けOK）")
    tsv = out_df.fillna("").astype(str).to_csv(sep="\t", index=False)
    st.text_area("下を全選択してコピー → Excelへ貼り付け", tsv, height=180)

    # CSVダウンロード
    csv_buf = io.StringIO()
    out_df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
    st.download_button(
        label="結果をCSVでダウンロード（UTF-8-SIG）",
        data=csv_buf.getvalue().encode("utf-8-sig"),
        file_name="sheet3_output.csv",
        mime="text/csv",
    )

    st.success(f"完了：一致件数 {len(out_df)//2} セット（出力行数 {len(out_df)}）")
