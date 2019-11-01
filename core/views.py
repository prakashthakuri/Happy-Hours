from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.utils import timezone
from .models import Item, OrderItem, Order, BillingAddress, Payment
from .forms import CheckoutForms
from django.conf import settings

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "product.html", context)


class CheckoutView(View):
    def get(self, *args, **kwargs):
        # form

        form = CheckoutForms()
        context = {
            'form': form
        }
        return render(self.request, "checkout.html", context)

    def post(self, *args, **kwargs):
        form = CheckoutForms(self.request.POST or None)

        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                city = form.cleaned_data.get('city')
                zip = form.cleaned_data.get('zip')
                # TODO: add functionalities for billing address and saving the info
                # same_shipping_address = form.cleaned_data.get('same_shipping_address')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    city=city,
                    zip=zip,

                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                # TODO add redirect to the selected payment option
                if payment_option == 'S':
                    return redirect('core:payment/stripe', payment_option='Stripe')
                elif payment_option == 'P':
                    return redirect('core:payment/paypal', payment_option='PayPal')
                elif payment_option == 'G':
                    return redirect('core:payment', payment_option='GiftCard')
                else:
                    messages.warning(self.request, "Invalid Payment Option Selected")
                    return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("core:order_summary")


# Payment
class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'order': order
        }
        return render(self.request, "payment.html", context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)

        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)

        try:
            charge = stripe.Charge.create(
                amount=order.get_total() * 100,  # multiplied by 100 because it is in cents
                currency="usd",
                source=token
            )
            # Logic

            # create a payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = int(order.get_total() * 100)
            payment.save()

            # Assign Order
            order.Ordered = True
            order.payment = payment
            order.save()

            # redirect
            messages.success("Your order has been Placed. Assigning Delivery Driver")
            return redirect("core:delivery")
            # Use Stripe's library to make requests...

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f"{err.get('message')}")
            return redirect("core:delivery")


        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "Rate Limit Error")
            return redirect("core:delivery")


        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, "Invalid Parameters")
            return redirect("core:delivery")


        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Not Authenticated")
            return redirect("core:delivery")


        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "Network Error")
            return redirect("core:delivery")


        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, "Something went wrong. You were not charged")
            return redirect("core:delivery")


        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.error(self.request, "A serious error has been occured. We have been notified.")
            return redirect("core:delivery")


class Delivery(View):
    template_name = "delivery.html"


class HomeView(ListView):
    model = Item
    paginate_by = 15
    template_name = "home.html"


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


@login_required()
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order_summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order_summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order_summary")


@login_required()
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order_summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:order_summary")
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:order_summary")


@login_required()
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)

            messages.info(request, "This item quantity was updated.")
            return redirect("core:order_summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)
