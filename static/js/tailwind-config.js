tailwind.config = {
    theme: {
        extend: {
            fontFamily: {
                display: ['"Space Grotesk"', 'sans-serif'],
                sans: ['"Manrope"', 'sans-serif'],
            },
            colors: {
                purple: {
                    500: '#7C3AED',
                    600: '#6D28D9',
                    700: '#5B21B6',
                },
                fuchsia: {
                    400: '#F059D0',
                    500: '#E01FB8',
                    600: '#B91393',
                },
                lime: {
                    300: '#D4F84A',
                    400: '#C2F229',
                },
                cyan: {
                    400: '#3DE0D0',
                },
            },
            boxShadow: {
                brutal: '5px 5px 0 0 #000',
                'brutal-sm': '3px 3px 0 0 #000',
                'brutal-lg': '8px 8px 0 0 #000',
                'brutal-fuchsia': '5px 5px 0 0 #E01FB8',
                'brutal-purple': '5px 5px 0 0 #7C3AED',
            },
            keyframes: {
                wiggle: {
                    '0%, 100%': { transform: 'rotate(-3deg)' },
                    '50%': { transform: 'rotate(3deg)' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
                    '50%': { transform: 'translateY(-14px) rotate(4deg)' },
                },
                popIn: {
                    '0%': { transform: 'scale(0.85)', opacity: '0' },
                    '60%': { transform: 'scale(1.04)', opacity: '1' },
                    '100%': { transform: 'scale(1)' },
                },
                blobMove: {
                    '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
                    '33%': { transform: 'translate(30px, -40px) scale(1.1)' },
                    '66%': { transform: 'translate(-25px, 25px) scale(0.95)' },
                },
                gradientShift: {
                    '0%, 100%': { backgroundPosition: '0% 50%' },
                    '50%': { backgroundPosition: '100% 50%' },
                },
                shake: {
                    '0%, 100%': { transform: 'translateX(0)' },
                    '20%, 60%': { transform: 'translateX(-6px)' },
                    '40%, 80%': { transform: 'translateX(6px)' },
                },
            },
            animation: {
                wiggle: 'wiggle 0.5s ease-in-out infinite',
                float: 'float 6s ease-in-out infinite',
                'float-slow': 'float 9s ease-in-out infinite',
                popIn: 'popIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both',
                blob: 'blobMove 12s ease-in-out infinite',
                gradient: 'gradientShift 6s ease infinite',
                shake: 'shake 0.4s ease-in-out',
            },
        },
    },
};
