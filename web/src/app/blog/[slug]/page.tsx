import type { Metadata } from "next";
import { BlogDetailClient } from "./blog-detail-client";
import { getPost } from "@/lib/blog-store";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://tnvgold.vercel.app";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) {
    return { title: "Post not found" };
  }
  return {
    title: post.title.vi,
    description: post.excerpt.vi,
    openGraph: {
      title: post.title.vi,
      description: post.excerpt.vi,
      type: "article",
      publishedTime: new Date(post.publishedAt).toISOString(),
      images: [`${SITE_URL}/api/og?title=${encodeURIComponent(post.title.vi)}&subtitle=${encodeURIComponent(post.excerpt.vi)}&type=blog`],
    },
    alternates: {
      canonical: `/blog/${slug}`,
    },
  };
}

export default async function BlogDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);

  // JSON-LD Article schema
  const jsonLd = post
    ? {
        "@context": "https://schema.org",
        "@type": "Article",
        headline: post.title.vi,
        description: post.excerpt.vi,
        datePublished: new Date(post.publishedAt).toISOString(),
        dateModified: new Date(post.publishedAt).toISOString(),
        author: { "@type": "Person", name: post.author },
        publisher: {
          "@type": "Organization",
          name: "TNV Gold",
          logo: { "@type": "ImageObject", url: `${SITE_URL}/favicon.ico` },
        },
        mainEntityOfPage: `${SITE_URL}/blog/${slug}`,
        inLanguage: "vi-VN",
      }
    : null;

  return (
    <>
      {jsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      )}
      <BlogDetailClient slug={slug} />
    </>
  );
}
