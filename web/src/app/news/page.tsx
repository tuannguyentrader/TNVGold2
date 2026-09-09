import type { Metadata } from "next";
import { NewsListClient } from "./news-list-client";

export const metadata: Metadata = {
  title: "Tin tức thị trường Vàng — Gold News",
  description:
    "Lịch kinh tế USD, tin tức quan trọng ảnh hưởng đến giá vàng XAUUSD. Cập nhật tự động từ ForexFactory.",
  alternates: {
    canonical: "/news",
  },
};

export default function NewsPage() {
  return <NewsListClient />;
}
