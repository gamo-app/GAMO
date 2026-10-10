from workers import fetch
import hashlib
import os


    
    

#----------------------------------------#





'''
trigger de sql (puede que esté algo mal)

CREATE TRIGGER set_payment_status
AFTER UPDATE ON deudas_pagos
FOR EACH ROW
BEGIN
    IF NEW.fecha_pago is not NULL and NEW.fecha_pago != "" THEN
        UPDATE socio SET estado_pago = "Al día"
END
'''




