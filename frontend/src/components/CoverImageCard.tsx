type CoverImageCardProps = {
  src: string;
  alt: string;
  variant?: 'detail' | 'list' | 'featured';
};

export default function CoverImageCard({
  src,
  alt,
  variant = 'detail',
}: CoverImageCardProps) {
  if (variant === 'list') {
    return (
      <div className="flex h-full items-center justify-center py-1">
        <div className="inline-flex max-w-full items-center justify-center rounded-[0.8rem] bg-white/86 px-1.5 py-1 shadow-[0_10px_24px_-24px_rgba(15,23,42,0.22)]">
          <img
            src={src}
            alt={alt}
            className="max-h-[4.4rem] w-auto max-w-full object-contain sm:max-h-[4.9rem]"
            loading="lazy"
          />
        </div>
      </div>
    );
  }

  if (variant === 'featured') {
    return (
      <div className="flex min-h-[100px] items-center justify-center rounded-[0.95rem] bg-slate-50/65 px-2 py-2">
        <img
          src={src}
          alt={alt}
          className="max-h-[6rem] w-auto max-w-full object-contain sm:max-h-[6.6rem]"
          loading="lazy"
        />
      </div>
    );
  }

  return (
    <div className="flex min-h-[228px] items-center justify-center rounded-[1.3rem] bg-[linear-gradient(180deg,rgba(248,250,252,0.85),rgba(255,255,255,0.96))] px-5 py-6 sm:min-h-[252px] sm:px-6 sm:py-7">
      <img
        src={src}
        alt={alt}
        className="max-h-[13.25rem] w-auto max-w-full object-contain sm:max-h-[14.5rem]"
        loading="lazy"
      />
    </div>
  );
}
