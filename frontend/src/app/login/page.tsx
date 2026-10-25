import type { Metadata } from 'next';
import LoginForm from './LoginForm';
import './login.css';

export const metadata: Metadata = { title: 'Sign in · StoreScout', description: 'Sign in to plan your next retail location with StoreScout.' };
export default function LoginPage() { return <LoginForm/>; }
