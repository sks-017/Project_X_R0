class BayesUpdater:
    def __init__(self, prior=0.01):
        self.prior = prior

    def update(self, p_e_given_f, p_e_given_not_f):
        """
        Update the prior probability based on new evidence.
        p_e_given_f: P(Evidence | Failure)
        p_e_given_not_f: P(Evidence | ~Failure)
        """
        p_f = self.prior
        num = p_e_given_f * p_f
        den = num + p_e_given_not_f * (1 - p_f)
        
        # Avoid division by zero
        if den == 0:
            return p_f
            
        posterior = num / den
        self.prior = posterior
        return posterior

if __name__ == "__main__":
    # Example usage
    updater = BayesUpdater(prior=0.02)
    print(f"Initial Prior: {updater.prior}")
    
    # Evidence: High temperature (Strong indicator of failure)
    new_prob = updater.update(0.8, 0.1)
    print(f"After High Temp: {new_prob:.4f}")
    
    # Evidence: Normal vibration (Weak indicator of health)
    new_prob = updater.update(0.4, 0.6)
    print(f"After Normal Vib: {new_prob:.4f}")
