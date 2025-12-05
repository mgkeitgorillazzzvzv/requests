export function capitalizeFirstLetter(string: string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

export function formatDateWithoutSeconds(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

export function getFullName(user: { first_name: string; last_name: string } | null | undefined): string {
    if (!user) {
        return 'Анонимная заявка';
    }
    return `${user.first_name} ${user.last_name}`.trim();
}