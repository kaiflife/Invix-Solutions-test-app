import Script from 'next/script';

type Product = {
  id: string;
  title: string;
  image_url: string;
};

// Функция для получения товаров
async function getProducts(): Promise<Product[]> {
  // Обращаемся к нашему FastAPI внутри Docker-сети
  const res = await fetch('http://backend:8000/api/products', {
    cache: 'no-store', // Чтобы данные всегда были свежими
  });

  if (!res.ok) {
    throw new Error('Failed to fetch products');
  }

  return res.json();
}

export default async function CatalogPage() {
  const products = await getProducts();

  return (
    <main style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      {/* Скрипт загрузится после гидратации */}
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" />
      
      <h1>Каталог</h1>
      
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginTop: '20px' }}>
        {products.length === 0 ? (
          <p>Товаров пока нет.</p>
        ) : (
          products.map((product) => (
              <div key={product.id} style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '8px', width: '200px' }}>
                <img 
                  src={product.image_url}
                  alt={product.title} 
                  style={{ width: '100%', height: '200px', objectFit: 'cover', borderRadius: '4px' }} 
                />
                <h2 style={{ fontSize: '18px', marginTop: '10px' }}>{product.title}</h2>
              </div>
            )
          )
        )}
      </div>
    </main>
  );
}