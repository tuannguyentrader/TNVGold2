import type { Metadata } from "next";
import { BlogListClient } from "./blog-list-client";

export const metadata: Metadata = {
  title: "Blog & Phân tích Vàng XAUUSD",
  description:
    "Bài viết phân tích XAUUSD, tin tức vàng, hướng dẫn giao dịch. Cập nhật tự động hàng giờ từ TNV Gold AI.",
  alternates: {
    canonical: "/blog",
  },
};

export default function BlogPage() {
  return <BlogListClient />;
}
