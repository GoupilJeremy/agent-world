# 📄 Agent World - Pagination Service
# Version: 0.4.2 (Épic 8 - Performance)
# Description: Service de pagination pour les endpoints API

"""
Pagination Service for Agent World API.

Ce module fournit des utilitaires pour paginer les résultats des requêtes,
réduisant ainsi la charge sur le serveur et améliorant les performances.
"""

from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from flask import request

T = TypeVar("T")


class PaginationResult(Generic[T]):
    """Résultat paginé avec métadonnées."""

    def __init__(
        self, items: List[T], total: int, page: int, per_page: int, total_pages: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.total_pages = total_pages

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire pour l'API."""
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "per_page": self.per_page,
                "total_pages": self.total_pages,
                "has_next": self.page < self.total_pages,
                "has_prev": self.page > 1,
            },
        }


class PaginationService:
    """Service de pagination pour les requêtes API."""

    DEFAULT_PER_PAGE = 20
    MAX_PER_PAGE = 100

    @staticmethod
    def get_pagination_params() -> Tuple[int, int]:
        """
        Récupère les paramètres de pagination depuis la requête.

        Returns:
            Tuple de (page, per_page)
        """
        try:
            page = int(request.args.get("page", 1))
            page = max(1, page)
        except (ValueError, TypeError):
            page = 1

        try:
            per_page = int(
                request.args.get("per_page", PaginationService.DEFAULT_PER_PAGE)
            )
            per_page = max(1, min(per_page, PaginationService.MAX_PER_PAGE))
        except (ValueError, TypeError):
            per_page = PaginationService.DEFAULT_PER_PAGE

        return page, per_page

    @staticmethod
    def paginate(
        query: Any, page: Optional[int] = None, per_page: Optional[int] = None
    ) -> PaginationResult:
        """
        Applique la pagination à une requête SQLAlchemy ou une liste.

        Args:
            query: Requête SQLAlchemy ou liste à paginer
            page: Numéro de page (1-based)
            per_page: Nombre d'éléments par page

        Returns:
            PaginationResult avec les éléments et métadonnées
        """
        if page is None or per_page is None:
            page, per_page = PaginationService.get_pagination_params()

        # Cas 1: C'est une requête SQLAlchemy
        if (
            hasattr(query, "count")
            and hasattr(query, "offset")
            and hasattr(query, "limit")
        ):
            total = query.count()
            total_pages = (total + per_page - 1) // per_page

            items = query.offset((page - 1) * per_page).limit(per_page).all()
            return PaginationResult(items, total, page, per_page, total_pages)

        # Cas 2: C'est une liste Python
        elif isinstance(query, list):
            total = len(query)
            total_pages = (total + per_page - 1) // per_page

            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            items = query[start_idx:end_idx]

            return PaginationResult(items, total, page, per_page, total_pages)

        else:
            raise ValueError(f"Cannot paginate type: {type(query)}")

    @staticmethod
    def paginate_list(
        items: List[T], page: Optional[int] = None, per_page: Optional[int] = None
    ) -> PaginationResult[T]:
        """
        Applique la pagination à une liste Python.

        Args:
            items: Liste à paginer
            page: Numéro de page (1-based)
            per_page: Nombre d'éléments par page

        Returns:
            PaginationResult avec les éléments et métadonnées
        """
        if page is None or per_page is None:
            page, per_page = PaginationService.get_pagination_params()

        total = len(items)
        total_pages = (total + per_page - 1) // per_page

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_items = items[start_idx:end_idx]

        return PaginationResult(paginated_items, total, page, per_page, total_pages)


def paginated_response(func):
    """
    Décorateur pour ajouter la pagination à un endpoint API.

    Usage:
        @paginated_response
        def get_agents():
            agents = Agent.get_all()
            return agents
    """
    from functools import wraps

    from flask import request

    def decorator(wrapped_func):
        @wraps(wrapped_func)
        def wrapper(*args, **kwargs):
            result = wrapped_func(*args, **kwargs)

            # Si le résultat est déjà un PaginationResult, le retourner tel quel
            if isinstance(result, PaginationResult):
                return result.to_dict()

            # Sinon, paginer le résultat
            page, per_page = PaginationService.get_pagination_params()

            # Convertir en liste si ce n'est pas déjà le cas
            if not isinstance(result, list):
                result = [result]

            paginated = PaginationService.paginate_list(result, page, per_page)
            return paginated.to_dict()

        return wrapper

    return decorator
