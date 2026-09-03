import type { Metadata } from "next";
import { NewsListClient } from "./news-list-client";

export const metadata: Metadata = {
  title: "Tin tức thị trường Vàng",
  description:
    "Lịch kinh tế USD, tin tức quan trọng ảnh hưởng đến giá vàng XAUUSD. Cập nhật tự động từ ForexFactory.",
  alternates: {
    canonical: "/tin-tuc",
  },
};

export default function NewsPage() {
  return <NewsListClient />;
}
