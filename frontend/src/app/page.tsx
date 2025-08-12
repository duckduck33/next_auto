'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    // 로그인 상태 확인
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    
    if (isLoggedIn === 'true') {
      // 로그인된 경우 메인 페이지로
      router.push('/dashboard');
    } else {
      // 로그인되지 않은 경우 로그인 페이지로
      router.push('/login');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-white">리다이렉트 중...</div>
    </div>
  );
}
