from django.utils.translation import gettext_lazy as _

from import_export import fields, resources

from apps.challenge.models import Invoice


class InvoiceResource(resources.ModelResource):
    canton = fields.Field(
        column_name=_("Canton de la facture"), attribute="organization__address_canton"
    )
    month = fields.Field(
        column_name=_("Mois de la facture"), attribute="month_of_the_invoice"
    )
    invoice_nb = fields.Field(column_name=_("N° de la facture"), attribute="ref")
    org_name = fields.Field(
        column_name=_("Nom de l'établissement"), attribute="organization__name"
    )
    total_participants = fields.Field(
        column_name=_("Total participants"), attribute="sum_nb_participants"
    )
    cost_per_participant = fields.Field(
        column_name=_("Coût par participant"),
        attribute="settings__cost_per_participant",
    )
    total_cost_participants = fields.Field(
        column_name=_("Total coût participants"), attribute="sum_cost_participants"
    )
    total_nb_bikes = fields.Field(
        column_name=_("Total vélos"), attribute="adjusted_sum_of_bikes"
    )
    cost_per_bike = fields.Field(
        column_name=_("Coût par vélo"), attribute="settings__cost_per_bike"
    )
    total_cost_bikes = fields.Field(
        column_name=_("Total coût vélos"), attribute="sum_cost_bikes_reduced"
    )
    invoice_total = fields.Field(
        column_name=_("Montant total de la facture"), attribute="sum_cost"
    )

    class Meta:
        model = Invoice
        fields = "__all__"
