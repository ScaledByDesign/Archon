#!/usr/bin/env python3
"""
Add comprehensive Next.js knowledge to Weaviate collections for Elysia RAG.
This script populates the Knowledge, Documents, and CodeSnippets collections
with Next.js documentation, best practices, and code examples.
"""

import weaviate
from datetime import datetime
from typing import List, Dict, Any
import json

# Connect to Weaviate using v4 client (skip init checks for simplicity)
client = weaviate.connect_to_local(host="localhost", port=7080, skip_init_checks=True)

def add_knowledge_articles():
    """Add Next.js knowledge articles to the Knowledge collection"""
    
    knowledge_articles = [
        {
            "title": "Next.js App Router Fundamentals",
            "content": """Next.js App Router is built on React Server Components and introduces a new paradigm for building React applications. Key concepts include:

1. **File-based Routing**: The app directory uses folders to define routes. Each folder represents a route segment.

2. **Server Components**: By default, components in the app directory are React Server Components, which run on the server.

3. **Client Components**: Use 'use client' directive at the top of files to mark components as Client Components.

4. **Layouts**: Create shared UI that persists across multiple pages using layout.js files.

5. **Pages**: Create unique UI for routes using page.js files.

6. **Loading and Error States**: Create loading.js for loading UI and error.js for error boundaries.

7. **Route Groups**: Use parentheses (folder) to organize routes without affecting the URL structure.

8. **Dynamic Routes**: Use square brackets [slug] to create dynamic route segments.

9. **Nested Routing**: The app directory supports nested routing with nested folders.

10. **Parallel Routes**: Use @folder convention to create parallel routes that render simultaneously.""",
            "summary": "Comprehensive guide to Next.js App Router fundamentals, covering file-based routing, Server Components, and modern React patterns.",
            "topic": "Next.js Routing",
            "keywords": ["nextjs", "app router", "server components", "routing", "react", "file-based routing"],
            "url": "https://nextjs.org/docs/app",
            "last_updated": datetime.now().isoformat() + "Z"
        },
        {
            "title": "Next.js Data Fetching Patterns",
            "content": """Next.js provides multiple patterns for data fetching, optimized for different use cases:

1. **Server-Side Rendering (SSR)**:
   - Use async Server Components to fetch data at request time
   - Data is fetched on the server for each request
   - Good for dynamic content that changes frequently

2. **Static Site Generation (SSG)**:
   - Data is fetched at build time
   - Pages are pre-rendered as static HTML
   - Excellent for content that doesn't change often

3. **Incremental Static Regeneration (ISR)**:
   - Combines benefits of SSG and SSR
   - Pages are statically generated but can be updated without rebuilding
   - Use revalidate option to control update frequency

4. **Client-Side Fetching**:
   - Fetch data in Client Components using useEffect or SWR/React Query
   - Good for user-specific data or real-time updates

5. **API Routes**:
   - Create backend API endpoints in the app/api directory
   - Handle GET, POST, PUT, DELETE requests
   - Perfect for form submissions and external API proxy

6. **Parallel Data Fetching**:
   - Fetch multiple data sources simultaneously
   - Use Promise.all() or concurrent async calls
   - Improves performance by reducing waterfall requests

7. **Streaming and Suspense**:
   - Stream UI components as they load
   - Use Suspense boundaries for better loading experience
   - Show loading states for specific parts of the page""",
            "summary": "Complete guide to data fetching patterns in Next.js, including SSR, SSG, ISR, and client-side strategies.",
            "topic": "Next.js Data Fetching",
            "keywords": ["nextjs", "data fetching", "ssr", "ssg", "isr", "api routes", "streaming", "suspense"],
            "url": "https://nextjs.org/docs/app/building-your-application/data-fetching",
            "last_updated": datetime.now().isoformat() + "Z"
        },
        {
            "title": "Next.js Performance Optimization",
            "content": """Next.js provides built-in optimizations and tools for maximum performance:

1. **Image Optimization**:
   - Use next/image component for automatic optimization
   - Lazy loading, responsive images, and modern formats
   - Priority loading for above-the-fold images

2. **Font Optimization**:
   - Use next/font for automatic font optimization
   - Eliminates layout shift and improves loading performance
   - Self-host Google Fonts with zero requests to Google

3. **Bundle Optimization**:
   - Automatic code splitting at the route level
   - Dynamic imports for client-side code splitting
   - Tree shaking removes unused code automatically

4. **Caching Strategies**:
   - Browser cache, CDN cache, and Next.js cache
   - Static file caching with immutable files
   - API route response caching with headers

5. **Core Web Vitals**:
   - Built-in Web Vitals reporting
   - Optimize Largest Contentful Paint (LCP)
   - Improve First Input Delay (FID) and Cumulative Layout Shift (CLS)

6. **Static Analysis**:
   - ESLint plugin for Next.js best practices
   - Bundle analyzer to identify large dependencies
   - Performance monitoring and metrics

7. **Edge Runtime**:
   - Run API routes and middleware on the edge
   - Faster response times globally
   - Reduced cold start times for serverless functions""",
            "summary": "Advanced techniques for optimizing Next.js applications for maximum performance and Core Web Vitals.",
            "topic": "Next.js Performance",
            "keywords": ["nextjs", "performance", "optimization", "web vitals", "caching", "bundle", "edge runtime"],
            "url": "https://nextjs.org/docs/app/building-your-application/optimizing",
            "last_updated": datetime.now().isoformat() + "Z"
        },
        {
            "title": "Next.js Authentication Patterns",
            "content": """Comprehensive guide to implementing authentication in Next.js applications:

1. **NextAuth.js Integration**:
   - Industry-standard authentication library for Next.js
   - Supports OAuth providers (Google, GitHub, etc.)
   - Built-in session management and security

2. **JWT Authentication**:
   - JSON Web Tokens for stateless authentication
   - Store tokens in httpOnly cookies for security
   - Implement token refresh patterns

3. **Session Management**:
   - Server-side session storage
   - Database session stores (Redis, PostgreSQL)
   - Session expiration and cleanup

4. **Route Protection**:
   - Middleware for route-level authentication
   - Server Component authentication checks
   - Redirect patterns for unauthenticated users

5. **API Route Security**:
   - Authenticate API routes with middleware
   - Role-based access control (RBAC)
   - Rate limiting and security headers

6. **SSR Authentication**:
   - Server-side authentication for initial page load
   - Hydration considerations with authentication state
   - Preventing authentication flicker

7. **Database Integration**:
   - User storage with Prisma, Supabase, or custom solutions
   - Profile management and user preferences
   - Multi-tenant authentication patterns""",
            "summary": "Complete authentication implementation guide for Next.js, covering NextAuth.js, JWT, sessions, and security best practices.",
            "topic": "Next.js Authentication",
            "keywords": ["nextjs", "authentication", "nextauth", "jwt", "sessions", "security", "oauth"],
            "url": "https://nextjs.org/docs/app/building-your-application/authentication",
            "last_updated": datetime.now().isoformat() + "Z"
        },
        {
            "title": "Next.js Deployment and Production",
            "content": """Best practices for deploying Next.js applications to production:

1. **Vercel Deployment**:
   - Native platform for Next.js applications
   - Automatic deployments from Git
   - Edge functions and global CDN
   - Built-in analytics and monitoring

2. **Docker Deployment**:
   - Containerize Next.js applications
   - Multi-stage builds for optimization
   - Production-ready Dockerfile examples
   - Kubernetes deployment patterns

3. **Static Export**:
   - Export static HTML files
   - Deploy to any static hosting provider
   - CDN integration for global distribution
   - Build-time optimizations

4. **Self-hosting Options**:
   - Node.js server deployment
   - PM2 for process management
   - Nginx reverse proxy configuration
   - Load balancing strategies

5. **Environment Configuration**:
   - Environment variable management
   - Production vs development configurations
   - Secret management and security
   - Configuration validation

6. **Monitoring and Analytics**:
   - Performance monitoring setup
   - Error tracking with Sentry
   - User analytics integration
   - Custom metrics and dashboards

7. **CI/CD Pipelines**:
   - GitHub Actions workflows
   - Automated testing and deployment
   - Preview deployments for pull requests
   - Rollback strategies and health checks""",
            "summary": "Production deployment guide for Next.js applications, covering Vercel, Docker, static export, and CI/CD best practices.",
            "topic": "Next.js Deployment",
            "keywords": ["nextjs", "deployment", "production", "vercel", "docker", "static export", "cicd"],
            "url": "https://nextjs.org/docs/app/building-your-application/deploying",
            "last_updated": datetime.now().isoformat() + "Z"
        }
    ]
    
    # Add articles to Knowledge collection
    knowledge_collection = client.collections.get("Knowledge")
    for article in knowledge_articles:
        knowledge_collection.data.insert(article)
        print(f"Added Knowledge article: {article['title']}")

def add_code_snippets():
    """Add Next.js code examples to the CodeSnippets collection"""
    
    code_snippets = [
        {
            "title": "Basic App Router Layout",
            "code": """import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'My Next.js App',
  description: 'Built with Next.js App Router',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-blue-600 text-white p-4">
          <h1>My App</h1>
        </nav>
        <main className="container mx-auto py-8">
          {children}
        </main>
      </body>
    </html>
  )
}""",
            "language": "typescript",
            "description": "Root layout component using Next.js App Router with Tailwind CSS styling and Inter font optimization.",
            "tags": ["nextjs", "app-router", "layout", "typescript", "tailwind"],
            "source_file": "app/layout.tsx",
            "created_at": datetime.now().isoformat() + "Z"
        },
        {
            "title": "Server Component with Data Fetching",
            "code": """import { notFound } from 'next/navigation'

interface User {
  id: number
  name: string
  email: string
}

async function getUser(id: string): Promise<User> {
  const res = await fetch(`https://api.example.com/users/${id}`, {
    next: { revalidate: 60 } // Revalidate every 60 seconds
  })
  
  if (!res.ok) {
    throw new Error('Failed to fetch user')
  }
  
  return res.json()
}

export default async function UserProfile({ 
  params 
}: { 
  params: { id: string } 
}) {
  const user = await getUser(params.id)
  
  if (!user) {
    notFound()
  }
  
  return (
    <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
      <h1 className="text-2xl font-bold text-gray-800">{user.name}</h1>
      <p className="text-gray-600">{user.email}</p>
      <div className="mt-4">
        <span className="text-sm text-gray-500">User ID: {user.id}</span>
      </div>
    </div>
  )
}

export async function generateStaticParams() {
  const users = await fetch('https://api.example.com/users')
  const userList = await users.json()
  
  return userList.map((user: User) => ({
    id: user.id.toString(),
  }))
}""",
            "language": "typescript",
            "description": "Server Component that fetches user data with ISR, includes error handling and static generation.",
            "tags": ["nextjs", "server-components", "data-fetching", "isr", "typescript"],
            "source_file": "app/users/[id]/page.tsx",
            "created_at": datetime.now().isoformat() + "Z"
        },
        {
            "title": "API Route with Authentication",
            "code": """import { NextRequest, NextResponse } from 'next/server'
import { verify } from 'jsonwebtoken'
import { cookies } from 'next/headers'

interface User {
  id: string
  email: string
  role: string
}

async function verifyToken(token: string): Promise<User | null> {
  try {
    const payload = verify(token, process.env.JWT_SECRET!) as any
    return payload.user
  } catch {
    return null
  }
}

export async function GET(request: NextRequest) {
  const cookieStore = cookies()
  const token = cookieStore.get('auth-token')?.value
  
  if (!token) {
    return NextResponse.json(
      { error: 'Authentication required' }, 
      { status: 401 }
    )
  }
  
  const user = await verifyToken(token)
  if (!user) {
    return NextResponse.json(
      { error: 'Invalid token' }, 
      { status: 401 }
    )
  }
  
  // Fetch user-specific data
  const userData = await getUserData(user.id)
  
  return NextResponse.json({
    user: {
      id: user.id,
      email: user.email,
      role: user.role
    },
    data: userData
  })
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Validate request body
    if (!body.name || !body.email) {
      return NextResponse.json(
        { error: 'Name and email are required' },
        { status: 400 }
      )
    }
    
    // Create user logic here
    const newUser = await createUser(body)
    
    return NextResponse.json(
      { user: newUser },
      { status: 201 }
    )
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

async function getUserData(userId: string) {
  // Database query logic
  return { /* user data */ }
}

async function createUser(data: any) {
  // Database creation logic
  return { /* created user */ }
}""",
            "language": "typescript",
            "description": "API route with JWT authentication, request validation, and error handling for both GET and POST methods.",
            "tags": ["nextjs", "api-routes", "authentication", "jwt", "typescript"],
            "source_file": "app/api/users/route.ts",
            "created_at": datetime.now().isoformat() + "Z"
        },
        {
            "title": "Client Component with State Management",
            "code": """'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface TodoItem {
  id: number
  text: string
  completed: boolean
}

export default function TodoList() {
  const [todos, setTodos] = useState<TodoItem[]>([])
  const [newTodo, setNewTodo] = useState('')
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  
  useEffect(() => {
    fetchTodos()
  }, [])
  
  const fetchTodos = async () => {
    try {
      const response = await fetch('/api/todos')
      if (response.ok) {
        const data = await response.json()
        setTodos(data.todos)
      }
    } catch (error) {
      console.error('Failed to fetch todos:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const addTodo = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTodo.trim()) return
    
    try {
      const response = await fetch('/api/todos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: newTodo }),
      })
      
      if (response.ok) {
        const data = await response.json()
        setTodos(prev => [...prev, data.todo])
        setNewTodo('')
      }
    } catch (error) {
      console.error('Failed to add todo:', error)
    }
  }
  
  const toggleTodo = async (id: number) => {
    const todo = todos.find(t => t.id === id)
    if (!todo) return
    
    try {
      const response = await fetch(`/api/todos/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ completed: !todo.completed }),
      })
      
      if (response.ok) {
        setTodos(prev =>
          prev.map(t =>
            t.id === id ? { ...t, completed: !t.completed } : t
          )
        )
      }
    } catch (error) {
      console.error('Failed to toggle todo:', error)
    }
  }
  
  if (loading) {
    return <div className="animate-pulse">Loading todos...</div>
  }
  
  return (
    <div className="max-w-md mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">My Todos</h2>
      
      <form onSubmit={addTodo} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={newTodo}
            onChange={(e) => setNewTodo(e.target.value)}
            placeholder="Add a new todo..."
            className="flex-1 px-3 py-2 border rounded-md"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Add
          </button>
        </div>
      </form>
      
      <ul className="space-y-2">
        {todos.map((todo) => (
          <li
            key={todo.id}
            className={`flex items-center gap-2 p-2 rounded ${
              todo.completed ? 'bg-green-50' : 'bg-gray-50'
            }`}
          >
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => toggleTodo(todo.id)}
              className="rounded"
            />
            <span
              className={`flex-1 ${
                todo.completed ? 'line-through text-gray-500' : ''
              }`}
            >
              {todo.text}
            </span>
          </li>
        ))}
      </ul>
      
      {todos.length === 0 && (
        <p className="text-gray-500 text-center py-8">No todos yet!</p>
      )}
    </div>
  )
}""",
            "language": "typescript",
            "description": "Client Component with state management, API integration, form handling, and optimistic UI updates for a todo list.",
            "tags": ["nextjs", "client-components", "react", "state-management", "forms", "typescript"],
            "source_file": "components/TodoList.tsx",
            "created_at": datetime.now().isoformat() + "Z"
        },
        {
            "title": "Middleware for Authentication and Redirects",
            "code": """import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { verify } from 'jsonwebtoken'

// Define protected and public routes
const protectedRoutes = ['/dashboard', '/profile', '/admin']
const publicRoutes = ['/login', '/register', '/', '/about']
const adminRoutes = ['/admin']

async function verifyToken(token: string) {
  try {
    const payload = verify(token, process.env.JWT_SECRET!) as any
    return payload.user
  } catch {
    return null
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('auth-token')?.value
  
  // Check if route is protected
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname.startsWith(route)
  )
  const isPublicRoute = publicRoutes.includes(pathname)
  const isAdminRoute = adminRoutes.some(route => 
    pathname.startsWith(route)
  )
  
  // Handle authentication
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('callbackUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }
  
  if (token) {
    const user = await verifyToken(token)
    
    if (!user) {
      // Invalid token - redirect to login
      const response = NextResponse.redirect(new URL('/login', request.url))
      response.cookies.delete('auth-token')
      return response
    }
    
    // Check admin access
    if (isAdminRoute && user.role !== 'admin') {
      return NextResponse.redirect(new URL('/unauthorized', request.url))
    }
    
    // Add user info to request headers for API routes
    const requestHeaders = new Headers(request.headers)
    requestHeaders.set('x-user-id', user.id)
    requestHeaders.set('x-user-role', user.role)
    
    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    })
  }
  
  // Add security headers
  const response = NextResponse.next()
  
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'origin-when-cross-origin')
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=()'
  )
  
  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
}""",
            "language": "typescript",
            "description": "Comprehensive middleware for authentication, role-based access control, security headers, and route protection.",
            "tags": ["nextjs", "middleware", "authentication", "security", "routing", "typescript"],
            "source_file": "middleware.ts",
            "created_at": datetime.now().isoformat() + "Z"
        }
    ]
    
    # Add code snippets to CodeSnippets collection
    snippets_collection = client.collections.get("CodeSnippets")
    for snippet in code_snippets:
        snippets_collection.data.insert(snippet)
        print(f"Added Code snippet: {snippet['title']}")

def add_documents():
    """Add Next.js documentation and guides to the Documents collection"""
    
    documents = [
        {
            "title": "Next.js 14 Getting Started Guide",
            "content": """# Getting Started with Next.js 14

Next.js is a React framework for building full-stack web applications. You use React Components to build user interfaces, and Next.js for additional features and optimizations.

## Installation

Create a new Next.js project:

```bash
npx create-next-app@latest my-app
cd my-app
npm run dev
```

## Project Structure

```
my-app/
├── app/                  # App Router (recommended)
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Home page
│   └── globals.css      # Global styles
├── public/              # Static files
├── next.config.js       # Next.js configuration
└── package.json
```

## Key Features

1. **App Router**: New routing system based on file structure
2. **Server Components**: React components that run on the server
3. **Image Optimization**: Built-in image optimization
4. **Font Optimization**: Automatic font loading optimization
5. **Built-in CSS Support**: CSS, Sass, CSS-in-JS support
6. **API Routes**: Build API endpoints
7. **Middleware**: Run code before requests complete
8. **TypeScript Support**: First-class TypeScript support

## First Steps

1. Update the home page in `app/page.tsx`
2. Add a new route by creating `app/about/page.tsx`
3. Create a layout in `app/layout.tsx`
4. Add global styles in `app/globals.css`
5. Deploy to Vercel with zero configuration

Next.js makes React development faster and more efficient with its powerful features and optimizations.""",
            "source": "Next.js Official Documentation",
            "category": "Tutorial",
            "metadata_json": json.dumps({
                "version": "14.0",
                "difficulty": "beginner",
                "topics": ["installation", "project-structure", "app-router"],
                "estimated_reading_time": "10 minutes"
            }),
            "created_at": datetime.now().isoformat() + "Z"
        },
        {
            "title": "Next.js App Router Migration Guide",
            "content": """# Migrating from Pages Router to App Router

The App Router is the recommended approach for new Next.js applications. Here's how to migrate from the Pages Router.

## Key Differences

### File Structure
- **Pages Router**: `pages/` directory
- **App Router**: `app/` directory

### Routing
- **Pages Router**: File-based routing with `pages/about.js`
- **App Router**: Folder-based routing with `app/about/page.js`

### Data Fetching
- **Pages Router**: `getServerSideProps`, `getStaticProps`
- **App Router**: Server Components with async/await

## Migration Steps

### 1. Create App Directory
```bash
mkdir app
```

### 2. Move Root Layout
Create `app/layout.tsx`:
```tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

### 3. Migrate Pages
- `pages/index.js` → `app/page.js`
- `pages/about.js` → `app/about/page.js`
- `pages/blog/[slug].js` → `app/blog/[slug]/page.js`

### 4. Update Data Fetching
Before (Pages Router):
```tsx
export async function getServerSideProps() {
  const data = await fetchData()
  return { props: { data } }
}
```

After (App Router):
```tsx
async function getData() {
  return await fetchData()
}

export default async function Page() {
  const data = await getData()
  return <div>{data}</div>
}
```

### 5. Migrate API Routes
- `pages/api/users.js` → `app/api/users/route.js`

### 6. Update Imports
- `next/router` → `next/navigation`
- `useRouter()` → `useRouter()` (different API)

## Best Practices

1. Migrate incrementally - both routers can coexist
2. Test thoroughly in development
3. Use TypeScript for better type safety
4. Follow the new conventions for layouts and loading states
5. Update your deployment configuration if needed""",
            "source": "Next.js Migration Guide",
            "category": "Guide",
            "metadata_json": json.dumps({
                "version": "14.0",
                "difficulty": "intermediate",
                "topics": ["migration", "app-router", "pages-router"],
                "estimated_reading_time": "15 minutes"
            }),
            "created_at": datetime.now().isoformat() + "Z"
        },
        {
            "title": "Next.js Performance Best Practices",
            "content": """# Next.js Performance Optimization Guide

Optimize your Next.js applications for maximum performance and user experience.

## Core Web Vitals Optimization

### Largest Contentful Paint (LCP)
- Use `next/image` for optimized images
- Implement proper loading strategies
- Optimize server response times
- Use CDN for static assets

### First Input Delay (FID)
- Minimize JavaScript bundle size
- Use dynamic imports for code splitting
- Optimize third-party scripts
- Implement proper loading priorities

### Cumulative Layout Shift (CLS)
- Reserve space for images and ads
- Use `next/font` for font optimization
- Avoid inserting content above existing content

## Image Optimization

```tsx
import Image from 'next/image'

// Optimized image with proper sizing
<Image
  src="/hero.jpg"
  alt="Hero image"
  width={800}
  height={600}
  priority // Load above-the-fold images first
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."
/>
```

## Bundle Optimization

### Dynamic Imports
```tsx
import dynamic from 'next/dynamic'

const DynamicComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>Loading...</p>,
  ssr: false // Client-side only
})
```

### Bundle Analysis
```bash
npm install --save-dev @next/bundle-analyzer
```

## Caching Strategies

### Static Generation
```tsx
// Pre-render at build time
export async function generateStaticParams() {
  return [{ id: '1' }, { id: '2' }]
}
```

### Revalidation
```tsx
// Revalidate every 60 seconds
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 60 }
})
```

## Database Optimization

### Connection Pooling
```tsx
import { Pool } from 'pg'

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20, // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})
```

### Query Optimization
- Use database indexes effectively
- Implement proper pagination
- Cache frequently accessed data
- Use database query optimization tools

## Monitoring and Analytics

### Real User Monitoring
```tsx
export function reportWebVitals(metric) {
  // Send to analytics service
  gtag('event', metric.name, {
    value: Math.round(metric.value),
    event_label: metric.id,
  })
}
```

### Performance Monitoring
- Use Vercel Analytics
- Implement custom performance tracking
- Monitor API response times
- Track error rates and user flows""",
            "source": "Next.js Performance Guide",
            "category": "Best Practices",
            "metadata_json": json.dumps({
                "version": "14.0",
                "difficulty": "advanced",
                "topics": ["performance", "optimization", "web-vitals", "caching"],
                "estimated_reading_time": "20 minutes"
            }),
            "created_at": datetime.now().isoformat() + "Z"
        }
    ]
    
    # Add documents to Documents collection
    documents_collection = client.collections.get("Documents")
    for doc in documents:
        documents_collection.data.insert(doc)
        print(f"Added Document: {doc['title']}")

def main():
    """Main function to add all Next.js knowledge to Weaviate"""
    print("Adding Next.js knowledge to Weaviate collections...")
    print()
    
    try:
        print("Adding Knowledge articles...")
        add_knowledge_articles()
        print()
        
        print("Adding Code snippets...")
        add_code_snippets()
        print()
        
        print("Adding Documents...")
        add_documents()
        print()
        
        print("Successfully added comprehensive Next.js knowledge to Weaviate!")
        print("Collections populated:")
        print("   - Knowledge: 5 articles on Next.js concepts")
        print("   - CodeSnippets: 5 practical code examples") 
        print("   - Documents: 3 comprehensive guides")
        print()
        print("You can now use Elysia to analyze and search this knowledge base!")
        
    except Exception as e:
        print(f"Error adding knowledge to Weaviate: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    main()